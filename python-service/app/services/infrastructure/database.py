"""
Database service for direct PostgreSQL access.
Handles connections and queries for queue system tables.
"""
import asyncpg
from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime, timezone
import json

from ...core.config import get_settings


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
        INSERT INTO evaluations (job_id, persona_id, vote_bool, confidence, reason_text, provider, model, latency_ms, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
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
                    evaluation.model,
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

    # Job Review Methods
    async def get_pending_review_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get jobs that are pending review (status = 'pending_review')."""
        if not self.initialized:
            await self.initialize()

        query = """
        SELECT id, site, job_url, title, company, location, description, 
               date_posted, ingested_at, status, updated_at
        FROM public.jobs 
        WHERE status = 'pending_review'
        ORDER BY ingested_at ASC
        LIMIT $1
        """

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get pending review jobs: {str(e)}")
            return []

    async def update_job_status(self, job_id: str, status: str) -> bool:
        """Update job status and updated_at timestamp."""
        if not self.initialized:
            await self.initialize()

        query = """
        UPDATE public.jobs 
        SET status = $2, updated_at = NOW()
        WHERE id = $1
        """

        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, job_id, status)
                return result == "UPDATE 1"
        except Exception as e:
            logger.error(f"Failed to update job status: {str(e)}")
            return False

    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID."""
        if not self.initialized:
            await self.initialize()

        query = """
        SELECT id, site, job_url, title, company, company_url, location_country,
               location_state, location_city, is_remote, job_type, compensation,
               interval, min_amount, max_amount, currency, salary_source,
               description, date_posted, ingested_at, status, updated_at, source_raw
        FROM public.jobs 
        WHERE id = $1
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, job_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get job by ID: {str(e)}")
            return None

    async def insert_job_review(self, job_id: str, review_data: Dict[str, Any]) -> bool:
        """Insert a job review result."""
        if not self.initialized:
            await self.initialize()

        # Validate job_id format
        import uuid
        try:
            uuid.UUID(job_id)
        except ValueError:
            logger.error(f"Invalid UUID format for job_id: {job_id}")
            return False

        query = """
        INSERT INTO public.job_reviews (
            job_id, recommend, confidence, rationale, personas, tradeoffs, 
            actions, sources, crew_output, processing_time_seconds, 
            crew_version, model_used, error_message, retry_count
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        ON CONFLICT (job_id) DO UPDATE SET
            recommend = EXCLUDED.recommend,
            confidence = EXCLUDED.confidence,
            rationale = EXCLUDED.rationale,
            personas = EXCLUDED.personas,
            tradeoffs = EXCLUDED.tradeoffs,
            actions = EXCLUDED.actions,
            sources = EXCLUDED.sources,
            crew_output = EXCLUDED.crew_output,
            processing_time_seconds = EXCLUDED.processing_time_seconds,
            crew_version = EXCLUDED.crew_version,
            model_used = EXCLUDED.model_used,
            error_message = EXCLUDED.error_message,
            retry_count = EXCLUDED.retry_count,
            updated_at = NOW()
        """

        try:
            # Add detailed logging for debugging
            logger.info(f"Attempting to insert job review for job_id: {job_id}")
            logger.debug(f"Review data keys: {list(review_data.keys())}")
            logger.debug(f"Recommend: {review_data.get('recommend')}, Confidence: {review_data.get('confidence')}")
            
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    query,
                    job_id,
                    review_data.get("recommend"),
                    review_data.get("confidence"),
                    review_data.get("rationale"),
                    json.dumps(review_data.get("personas")) if review_data.get("personas") else None,
                    json.dumps(review_data.get("tradeoffs")) if review_data.get("tradeoffs") else None,
                    json.dumps(review_data.get("actions")) if review_data.get("actions") else None,
                    json.dumps(review_data.get("sources")) if review_data.get("sources") else None,
                    json.dumps(review_data.get("crew_output")) if review_data.get("crew_output") else None,
                    review_data.get("processing_time_seconds"),
                    review_data.get("crew_version"),
                    review_data.get("model_used"),
                    review_data.get("error_message"),
                    review_data.get("retry_count", 0)
                )
                
                logger.info(f"Job review insert result: {result}")
                
                # Verify the insert worked by querying the record
                verify_query = "SELECT id FROM public.job_reviews WHERE job_id = $1"
                verify_result = await conn.fetchval(verify_query, job_id)
                
                if verify_result:
                    logger.info(f"Job review successfully inserted and verified for job_id: {job_id}")
                    return True
                else:
                    logger.error(f"Job review insert succeeded but verification failed for job_id: {job_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to insert job review for job_id {job_id}: {str(e)}")
            logger.error(f"Review data: {review_data}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    async def get_job_review(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job review by job ID."""
        if not self.initialized:
            await self.initialize()

        query = """
        SELECT id, job_id, recommend, confidence, rationale, personas, tradeoffs,
               actions, sources, crew_output, processing_time_seconds, crew_version,
               model_used, error_message, retry_count, created_at, updated_at
        FROM public.job_reviews 
        WHERE job_id = $1
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, job_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get job review: {str(e)}")
            return None

    async def get_reviewed_jobs(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "date_posted",
        sort_order: str = "DESC",
        recommendation: Optional[bool] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        company: Optional[str] = None,
        source: Optional[str] = None,
        is_remote: Optional[bool] = None,
        date_posted_after: Optional[datetime] = None,
        date_posted_before: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get jobs with their reviews, supporting pagination, sorting, and filtering.
        
        Returns:
            Dict containing 'jobs' list and 'total_count' int
        """
        if not self.initialized:
            await self.initialize()

        # Build WHERE conditions
        where_conditions = []
        params = []
        param_count = 0

        if recommendation is not None:
            param_count += 1
            where_conditions.append(f"jr.recommend = ${param_count}")
            params.append(recommendation)

        if min_score is not None:
            # For now, we'll use confidence as a proxy for score
            # In the future, this could be calculated from personas or other fields
            param_count += 1
            where_conditions.append(f"CASE WHEN jr.confidence = 'high' THEN 0.8 WHEN jr.confidence = 'medium' THEN 0.6 ELSE 0.4 END >= ${param_count}")
            params.append(min_score)

        if max_score is not None:
            param_count += 1
            where_conditions.append(f"CASE WHEN jr.confidence = 'high' THEN 0.8 WHEN jr.confidence = 'medium' THEN 0.6 ELSE 0.4 END <= ${param_count}")
            params.append(max_score)

        if company:
            param_count += 1
            where_conditions.append(f"j.company ILIKE ${param_count}")
            params.append(f"%{company}%")

        if source:
            param_count += 1
            where_conditions.append(f"j.site = ${param_count}")
            params.append(source)

        if is_remote is not None:
            param_count += 1
            where_conditions.append(f"j.is_remote = ${param_count}")
            params.append(is_remote)

        if date_posted_after:
            param_count += 1
            where_conditions.append(f"j.date_posted >= ${param_count}")
            params.append(date_posted_after)

        if date_posted_before:
            param_count += 1
            where_conditions.append(f"j.date_posted <= ${param_count}")
            params.append(date_posted_before)

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Validate sort parameters
        valid_sort_columns = {
            "date_posted": "j.date_posted",
            "company": "j.company",
            "title": "j.title", 
            "review_date": "jr.created_at",
            "recommendation": "jr.recommend"
        }
        
        sort_column = valid_sort_columns.get(sort_by, "j.date_posted")
        sort_order = "DESC" if sort_order.upper() == "DESC" else "ASC"

        # Query for total count
        count_query = f"""
        SELECT COUNT(*)
        FROM public.jobs j
        INNER JOIN public.job_reviews jr ON j.id = jr.job_id
        {where_clause}
        """

        # Main query with pagination
        data_query = f"""
        SELECT 
            j.id as job_id,
            j.title,
            j.company,
            j.location_city || COALESCE(', ' || j.location_state, '') || COALESCE(', ' || j.location_country, '') as location,
            j.job_url as url,
            j.date_posted,
            j.site as source,
            j.description,
            j.min_amount as salary_min,
            j.max_amount as salary_max,
            j.currency as salary_currency,
            j.is_remote,
            jr.recommend,
            jr.confidence,
            jr.rationale,
            jr.personas,
            jr.tradeoffs,
            jr.actions,
            jr.sources,
            jr.crew_version as reviewer,
            jr.created_at as review_date
        FROM public.jobs j
        INNER JOIN public.job_reviews jr ON j.id = jr.job_id
        {where_clause}
        ORDER BY {sort_column} {sort_order}
        LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """

        try:
            async with self.pool.acquire() as conn:
                # Get total count
                total_count = await conn.fetchval(count_query, *params)
                
                # Get paginated data
                params.extend([limit, offset])
                rows = await conn.fetch(data_query, *params)
                
                jobs = []
                for row in rows:
                    # Calculate alignment score from confidence
                    confidence_scores = {"high": 0.8, "medium": 0.6, "low": 0.4}
                    alignment_score = confidence_scores.get(row["confidence"], 0.4)
                    
                    job_data = {
                        "job": {
                            "job_id": str(row["job_id"]),
                            "title": row["title"],
                            "company": row["company"],
                            "location": row["location"] if row["location"].strip(", ") else None,
                            "url": row["url"],
                            "date_posted": row["date_posted"],
                            "source": row["source"],
                            "description": row["description"],
                            "salary_min": row["salary_min"],
                            "salary_max": row["salary_max"],
                            "salary_currency": row["salary_currency"],
                            "is_remote": row["is_remote"]
                        },
                        "review": {
                            "overall_alignment_score": alignment_score,
                            "recommendation": row["recommend"],
                            "confidence": row["confidence"],
                            "reviewer": row["reviewer"],
                            "review_date": row["review_date"],
                            "rationale": row["rationale"],
                            "personas": row["personas"],
                            "tradeoffs": row["tradeoffs"],
                            "actions": row["actions"],
                            "sources": row["sources"]
                        }
                    }
                    jobs.append(job_data)

                return {
                    "jobs": jobs,
                    "total_count": total_count or 0
                }

        except Exception as e:
            logger.error(f"Failed to get reviewed jobs: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"jobs": [], "total_count": 0}


def get_database_service() -> DatabaseService:
    """Create a new database service instance."""
    return DatabaseService()

