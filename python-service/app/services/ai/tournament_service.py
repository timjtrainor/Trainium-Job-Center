import os
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime, timezone
import uuid
import traceback

from app.services.infrastructure.database import DatabaseService
from app.services.ai.ai_service import AIService

class TournamentService:
    def __init__(self, db_service: DatabaseService, ai_service: AIService):
        self.db = db_service
        self.ai = ai_service

    async def audit_application_impact(self, job_application_id: Optional[str], user_id: str, days: int = 1) -> Optional[Dict[str, Any]]:
        """
        Triggered when a new job application is created or when recalculating.
        Re-ranks the networking leaderboard and returns an alert if a specific app ranks highly.
        """
        logger.info(f"Auditing tournament impact for application: {job_application_id}")
        
        try:
            # 0. Cleanup: Remove jobs where outreach started
            await self._cleanup_leaderboard()
            
            # 1. Fetch search context
            # We filter for jobs that haven't been 'Completed' or 'Archived' and are scored.
            candidates = await self._fetch_candidates(user_id, days=days)
            
            # 2. Fetch specific data for the current job (Pathology & Intel)
            new_job_intel = ""
            if job_application_id:
                new_job_intel_data = next((c for c in candidates if str(c.get("job_application_id")) == job_application_id), None)
                if new_job_intel_data:
                    new_job_intel = json.dumps(new_job_intel_data.get("job_problem_analysis_result"), default=str)

            # 3. Fetch current Leaderboard
            current_leaderboard = await self._fetch_current_leaderboard()
            
            # 4. Prepare re-rank context and Select Prompt
            if job_application_id:
                # SINGLE Audit Mode
                prompt_name = "networking/tournament-re-rank"
                variables = {
                    "NEW_APP_PATHOLOGY_INTEL": new_job_intel,
                    "CURRENT_LEADERBOARD_JSON": json.dumps(current_leaderboard, default=str)
                }
            else:
                # BULK Hub Rank mode
                prompt_name = "networking/tournament-bulk-rank"
                variables = {
                    "CANDIDATE_POOL_JSON": json.dumps(candidates, default=str)
                }
            
            # 5. Call LLM for Re-Ranking
            logger.info(f"Executing prompt: {prompt_name} for user {user_id}")
            result = self.ai.execute_prompt(
                prompt_name=prompt_name,
                variables=variables,
                user_id=user_id,
                trace_source="tournament-service"
            )
            
            if not result:
                logger.error(f"LLM returned no result for {prompt_name}")
                return None

            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse tournament result as JSON: {result[:200]}")
                    return None

            # 6. Process and Update Table
            new_ranks = result.get("leaderboard", [])
            alert_trigger = result.get("alert_trigger")
            strike_pov = result.get("strike_pov")

            if not new_ranks:
                logger.warning(f"LLM returned empty leaderboard for user {user_id}. Pool size was {len(candidates) if not job_application_id else 1}")
                # We still might want to clear the old leaderboard if it's a bulk refresh and pool is empty
                if not job_application_id:
                    await self._update_leaderboard([])
                return None
                
            logger.info(f"Successfully ranked {len(new_ranks)} opportunities. Updating leaderboard.")
            await self._update_leaderboard(new_ranks)
            
            # 7. Check for High Value Match Alert (STRIKE)
            if job_application_id and (alert_trigger == "STRIKE" or (strike_pov and not alert_trigger)):
                # Find the rank of the new job in the new list
                # Ensure we compare strings as IDs can be UUID objects or strings
                new_entry = next((e for e in new_ranks if str(e.get("job_application_id")) == str(job_application_id)), None)
                if new_entry:
                    logger.info(f"STRIKE detected for application {job_application_id} at rank {new_entry.get('rank')}")
                    return {
                        "type": "leaderboard_alert",
                        "rank": new_entry.get("rank"),
                        "pov_hook": strike_pov or new_entry.get("pov_hook"),
                        "is_high_value": True
                    }
                else:
                    logger.warning(f"STRIKE triggered but application {job_application_id} not found in new leaderboard ranks.")

            
            return {"success": True, "count": len(new_ranks)}

        except Exception as e:
            logger.error(f"Tournament service failure: {str(e)}")
            logger.error(traceback.format_exc())
            raise e

    async def recalculate_history(self, user_id: str, days: int = 1):
        """Batch utility to re-rank historical jobs."""
        logger.info(f"Recalculating tournament history for user {user_id} (last {days} days)")
        return await self.audit_application_impact(None, user_id, days=days)

    async def delete_from_leaderboard(self, job_application_id: str):
        """Manual removal of an application from the leaderboard."""
        if not self.db.initialized:
            await self.db.initialize()
            
        query = "DELETE FROM networking_leaderboard WHERE job_application_id = $1"
        async with self.db.pool.acquire() as conn:
            await conn.execute(query, job_application_id)
        
        # After deletion, we should ideally shift the others up, 
        # but a simple re-rank trigger is more robust.
        # logger.info(f"Removed {job_application_id} from leaderboard.")

    async def _fetch_candidates(self, user_id: str, days: int = 1) -> List[Dict[str, Any]]:
        """Fetch high-potential candidates for re-ranking within a time window."""
        if not self.db.initialized:
            await self.db.initialize()
            
        # Strategy:
        # 1. Get apps where status is NOT terminal ('Archived', 'Rejected', etc.)
        # 2. Exclude apps that already have outreach (messages/linkedin_engagements)
        # 3. Sort by strategic_fit_score desc
        # 4. Limit to 30
        
        query = """
        SELECT 
            ja.job_application_id, 
            ja.job_title, 
            ja.salary,
            ja.job_problem_analysis_result,
            ja.alignment_strategy
        FROM job_applications ja
        JOIN companies c ON ja.company_id = c.company_id
        LEFT JOIN statuses s ON ja.status_id = s.status_id
        WHERE ja.user_id = $1
          AND ja.date_applied >= NOW() - ($2 * interval '1 day')
          AND s.status_name = 'Step-4: Applied'
          AND ja.job_application_id NOT IN (
              SELECT DISTINCT job_application_id FROM messages WHERE job_application_id IS NOT NULL
          )
        ORDER BY ja.strategic_fit_score DESC NULLS LAST, ja.created_at DESC
        LIMIT 30
        """
        
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, days)
            # Ensure the output strictly contains only the 5 sovereign columns
            candidates = []
            for row in rows:
                candidate = {
                    "job_application_id": str(row["job_application_id"]),
                    "salary": row["salary"] or "Not specified",
                    "job_title": row["job_title"],
                    "job_problem_analysis_result": row["job_problem_analysis_result"] or {},
                    "alignment_strategy": row["alignment_strategy"] or {}
                }
                candidates.append(candidate)
            return candidates

    async def _fetch_current_leaderboard(self) -> List[Dict[str, Any]]:
        """Fetch current Top 10 rankings."""
        if not self.db.initialized:
            await self.db.initialize()
            
        query = """
        SELECT nl.rank, nl.job_application_id, ja.job_title, nl.pov_hook
        FROM networking_leaderboard nl
        JOIN job_applications ja ON nl.job_application_id = ja.job_application_id
        ORDER BY nl.rank ASC
        """
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def _update_leaderboard(self, new_ranks: List[Dict[str, Any]]):
        """Atomic update of the leaderboard table."""
        if not self.db.initialized:
            await self.db.initialize()
            
        async with self.db.pool.acquire() as conn:
            async with conn.transaction():
                # 1. Clear current leaderboard (simple approach for Top 10)
                await conn.execute("DELETE FROM networking_leaderboard")
                
                # 2. Insert new rankings
                for entry in new_ranks:
                    rank = entry.get("rank")
                    app_id = entry.get("job_application_id")
                    pov_hook = entry.get("pov_hook")
                    
                    if rank and app_id:
                        try:
                            # Validate and convert to UUID object for asyncpg
                            app_uuid = uuid.UUID(str(app_id))
                            await conn.execute(
                                "INSERT INTO networking_leaderboard (rank, job_application_id, pov_hook) VALUES ($1, $2, $3)",
                                int(rank), app_uuid, pov_hook
                            )
                        except (ValueError, TypeError):
                            logger.error(f"Invalid UUID or rank in tournament results: {app_id}, {rank}")
                            continue

    async def _cleanup_leaderboard(self):
        """Removes entries from the leaderboard if they now have outreach activity."""
        if not self.db.initialized:
            await self.db.initialize()
            
        query = """
        DELETE FROM networking_leaderboard nl
        WHERE nl.job_application_id IN (
            SELECT DISTINCT job_application_id FROM messages WHERE job_application_id IS NOT NULL
        )
        """
        async with self.db.pool.acquire() as conn:
            await conn.execute(query)

_tournament_service = None

def get_tournament_service() -> TournamentService:
    global _tournament_service
    if _tournament_service is None:
        from app.services.infrastructure.database import get_database_service
        from app.services.ai.ai_service import AIService
        db = get_database_service()
        ai = AIService()
        _tournament_service = TournamentService(db, ai)
    return _tournament_service
