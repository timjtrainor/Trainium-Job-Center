"""
Database service for direct PostgreSQL access.
Handles connections and queries for queue system tables.
"""
import asyncpg
from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime, timezone
import json

from ..core.config import get_settings


class DatabaseService:
    """Service for direct database access."""
    
    def __init__(self):
        self.settings = get_settings()
        self.pool: Optional[asyncpg.Pool] = None
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.settings.database_url,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            self.initialized = True
            logger.info("Database connection pool initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {str(e)}")
            return False

    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.initialized = False
            logger.info("Database connection pool closed")

    async def get_enabled_site_schedules(self) -> List[Dict[str, Any]]:
        """Get all enabled site schedules that are due for execution."""
        if not self.initialized:
            await self.initialize()
        
        query = """
        SELECT id, site_name, interval_minutes, payload, min_pause_seconds, 
               max_pause_seconds, max_retries, last_run_at, next_run_at
        FROM site_schedules 
        WHERE enabled = true 
        AND (next_run_at IS NULL OR next_run_at <= NOW())
        ORDER BY next_run_at NULLS FIRST
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def update_site_schedule_next_run(self, schedule_id: str, next_run_at: datetime) -> bool:
        """Update the next_run_at for a site schedule."""
        if not self.initialized:
            await self.initialize()
        
        query = """
        UPDATE site_schedules 
        SET next_run_at = $2, last_run_at = NOW(), updated_at = NOW()
        WHERE id = $1
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, schedule_id, next_run_at)
            return True
        except Exception as e:
            logger.error(f"Failed to update site schedule next_run_at: {str(e)}")
            return False

    async def create_scrape_run(self, run_id: str, site_schedule_id: Optional[str], 
                              task_id: str, trigger: str) -> Optional[str]:
        """Create a new scrape run record."""
        if not self.initialized:
            await self.initialize()
        
        query = """
        INSERT INTO scrape_runs (run_id, site_schedule_id, task_id, trigger)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(query, run_id, site_schedule_id, task_id, trigger)
            return str(result)
        except Exception as e:
            logger.error(f"Failed to create scrape run: {str(e)}")
            return None

    async def update_scrape_run_status(self, run_id: str, status: str,
                                     started_at: Optional[datetime] = None,
                                     finished_at: Optional[datetime] = None,
                                     requested_pages: Optional[int] = None,
                                     completed_pages: Optional[int] = None,
                                     errors_count: Optional[int] = None,
                                     task_id: Optional[str] = None,
                                     message: Optional[str] = None) -> bool:
        """Update scrape run status, task ID, and metrics."""
        if not self.initialized:
            await self.initialize()

        # Build dynamic update query
        updates = ["status = $2", "updated_at = NOW()"]
        params = [run_id, status]
        param_count = 3
        
        if started_at is not None:
            updates.append(f"started_at = ${param_count}")
            params.append(started_at)
            param_count += 1
            
        if finished_at is not None:
            updates.append(f"finished_at = ${param_count}")
            params.append(finished_at)
            param_count += 1
            
        if requested_pages is not None:
            updates.append(f"requested_pages = ${param_count}")
            params.append(requested_pages)
            param_count += 1
            
        if completed_pages is not None:
            updates.append(f"completed_pages = ${param_count}")
            params.append(completed_pages)
            param_count += 1
            
        if errors_count is not None:
            updates.append(f"errors_count = ${param_count}")
            params.append(errors_count)
            param_count += 1
            
        if task_id is not None:
            updates.append(f"task_id = ${param_count}")
            params.append(task_id)
            param_count += 1

        if message is not None:
            updates.append(f"message = ${param_count}")
            params.append(message)
            param_count += 1
        
        query = f"""
        UPDATE scrape_runs 
        SET {', '.join(updates)}
        WHERE run_id = $1
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, *params)
            return True
        except Exception as e:
            logger.error(f"Failed to update scrape run status: {str(e)}")
            return False

    async def get_scrape_run_by_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get scrape run details by run_id."""
        if not self.initialized:
            await self.initialize()
        
        query = """
        SELECT id, run_id, site_schedule_id, task_id, trigger, status,
               started_at, finished_at, requested_pages, completed_pages,
               errors_count, message, created_at, updated_at
        FROM scrape_runs 
        WHERE run_id = $1
        """
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, run_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get scrape run: {str(e)}")
            return None

    async def check_site_lock(self, site_name: str) -> bool:
        """Check if there's already a running scrape for this site."""
        if not self.initialized:
            await self.initialize()
        
        query = """
        SELECT COUNT(*) 
        FROM scrape_runs sr
        JOIN site_schedules ss ON sr.site_schedule_id = ss.id
        WHERE ss.site_name = $1 AND sr.status IN ('queued', 'running')
        """
        
        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval(query, site_name)
                return count > 0
        except Exception as e:
            logger.error(f"Failed to check site lock: {str(e)}")
            return True  # Err on the side of caution

    async def insert_persona_evaluation(self, evaluation: "PersonaEvaluation") -> bool:
        """Persist a persona evaluation result."""
        if not self.initialized:
            await self.initialize()

        query = """
        INSERT INTO evaluations (job_id, persona_id, vote_bool, confidence, reason_text, provider, latency_ms, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query,
                    evaluation.job_id,
                    evaluation.persona_id,
                    evaluation.vote_bool,
                    evaluation.confidence,
                    evaluation.reason_text,
                    evaluation.provider,
                    evaluation.latency_ms,
                    evaluation.created_at,
                )
            return True
        except Exception as e:
            logger.error(f"Failed to insert evaluation: {str(e)}")
            return False

    async def insert_decision(self, decision: "Decision") -> bool:
        """Persist final judge decision."""
        if not self.initialized:
            await self.initialize()

        query = """
        INSERT INTO decisions (job_id, final_decision_bool, confidence, reason_text, method, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        """

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query,
                    decision.job_id,
                    decision.final_decision_bool,
                    decision.confidence,
                    decision.reason_text,
                    decision.method,
                    decision.created_at,
                )
            return True
        except Exception as e:
            logger.error(f"Failed to insert decision: {str(e)}")
            return False

    async def get_user_resume_context(self, user_id: str) -> Dict[str, Any]:
        """Fetch default resume, standard job roles, and strategic narratives for a user."""
        if not self.initialized:
            await self.initialize()

        resume_q = (
            """
            SELECT r.resume_id, r.resume_name
            FROM strategic_narratives sn
            JOIN resumes r ON sn.default_resume_id = r.resume_id
            WHERE sn.user_id = $1
            LIMIT 1
            """
        )
        roles_q = "SELECT role_name FROM standard_job_roles WHERE user_id = $1"
        narratives_q = "SELECT narrative_summary FROM strategic_narratives WHERE user_id = $1"

        try:
            async with self.pool.acquire() as conn:
                resume_row = await conn.fetchrow(resume_q, user_id)
                roles_rows = await conn.fetch(roles_q, user_id)
                narratives_rows = await conn.fetch(narratives_q, user_id)
            return {
                "default_resume": dict(resume_row) if resume_row else None,
                "standard_job_roles": [r["role_name"] for r in roles_rows],
                "strategic_narratives": [n["narrative_summary"] for n in narratives_rows],
            }
        except Exception as e:
            logger.error(f"Failed to fetch resume context: {str(e)}")
            return {
                "default_resume": None,
                "standard_job_roles": [],
                "strategic_narratives": [],
            }


# Global instance
_database_service: Optional[DatabaseService] = None

def get_database_service() -> DatabaseService:
    """Get or create the global database service instance."""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
