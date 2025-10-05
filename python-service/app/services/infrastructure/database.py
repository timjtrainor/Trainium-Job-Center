"""
Database service for direct PostgreSQL access.
Handles connections and queries for queue system tables.
"""
import asyncpg
from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime, timezone
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ...core.config import get_settings


class DatabaseService:
    """Service for direct database access."""

    def __init__(self):
        self.settings = get_settings()
        self.pool: Optional[asyncpg.Pool] = None
        self.initialized = False

    @staticmethod
    def _deserialize_json_field(value: Any) -> Optional[Any]:
        """Convert JSON stored as text to native Python structures for API responses."""
        if value is None or isinstance(value, (list, dict)):
            return value

        if isinstance(value, str):
            trimmed_value = value.strip()
            if not trimmed_value:
                return None

            try:
                return json.loads(trimmed_value)
            except json.JSONDecodeError:
                logger.warning("Failed to deserialize JSON field", value=value)
                return None

        return None

    async def initialize(self) -> bool:
        """Initialize database connection pool with retry logic."""
        import asyncio

        for attempt in range(5):  # Retry up to 5 times
            try:
                self.pool = await asyncpg.create_pool(
                    self.settings.database_url,
                    min_size=1,
                    max_size=5,
                    command_timeout=15  # Reduced timeout
                )
                self.initialized = True
                logger.info("Database connection pool initialized")
                return True
            except Exception as e:
                error_msg = str(e)
                if "sorry, too many clients already" in error_msg:
                    wait_time = (attempt + 1) * 2  # 2, 4, 6, 8, 10 seconds
                    logger.warning(f"Too many clients, retrying in {wait_time}s (attempt {attempt + 1}/5)")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Failed to initialize database pool: {error_msg}")
                    return False

        logger.error("Failed to initialize database pool after 5 attempts")
        return False

    @staticmethod
    def _get_currency_symbol(currency: Optional[str]) -> str:
        """Return a currency symbol for common codes, fallback to '$'."""
        if not currency:
            return "$"

        currency_upper = currency.upper()
        symbol_map = {
            "USD": "$",
            "CAD": "$",
            "AUD": "$",
            "NZD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥"
        }

        return symbol_map.get(currency_upper, "$")

    def _format_salary_value(self, amount: Optional[Any], currency: Optional[str]) -> Optional[str]:
        """Format a numeric salary into a compact string (e.g., $90k)."""
        if amount is None:
            return None

        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, TypeError):
            return None

        symbol = self._get_currency_symbol(currency)
        abs_amount = decimal_amount.copy_abs()

        if abs_amount >= Decimal("1000"):
            value_in_thousands = (decimal_amount / Decimal("1000")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            value_str = format(value_in_thousands, "f").rstrip("0").rstrip(".")
            if not value_str:
                value_str = "0"
            return f"{symbol}{value_str}k"

        formatted_number = format(decimal_amount, ",")
        return f"{symbol}{formatted_number}"

    def _format_salary_range(
        self,
        salary_min: Optional[Any],
        salary_max: Optional[Any],
        currency: Optional[str]
    ) -> Optional[str]:
        """Create a human-readable salary range string."""
        formatted_min = self._format_salary_value(salary_min, currency)
        formatted_max = self._format_salary_value(salary_max, currency)

        if formatted_min and formatted_max:
            if formatted_min == formatted_max:
                return formatted_min
            return f"{formatted_min} - {formatted_max}"

        return formatted_min or formatted_max

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

    async def insert_persona_evaluation(self, evaluation: Dict[str, Any]) -> bool:
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

    async def insert_decision(self, decision: Dict[str, Any]) -> bool:
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
            actions, sources, overall_alignment_score, crew_output, processing_time_seconds,
            crew_version, model_used, error_message, retry_count
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        ON CONFLICT (job_id) DO UPDATE SET
            recommend = EXCLUDED.recommend,
            confidence = EXCLUDED.confidence,
            rationale = EXCLUDED.rationale,
            personas = EXCLUDED.personas,
            tradeoffs = EXCLUDED.tradeoffs,
            actions = EXCLUDED.actions,
            sources = EXCLUDED.sources,
            overall_alignment_score = EXCLUDED.overall_alignment_score,
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
                    review_data.get("overall_alignment_score"),  # Separate column for alignment score
                    # crew_output includes tldr_summary (but not overall_alignment_score since it's separate)
                    json.dumps({
                        **(review_data.get("crew_output") or {}),
                        "tldr_summary": review_data.get("tldr_summary")
                    }) if review_data.get("crew_output") or review_data.get("tldr_summary") else None,
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
               model_used, error_message, retry_count, created_at, updated_at,
               override_recommend, override_comment, override_by, override_at
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

    async def update_job_review_override(
        self, 
        job_id: str, 
        override_recommend: bool,
        override_comment: str,
        override_by: str = "system_admin"
    ) -> Optional[Dict[str, Any]]:
        """Update job review with human override data.
        
        Returns:
            Dict with job review data if found and updated successfully.
            None if job review not found for the given job_id.
            
        Raises:
            ValueError: If job_id is not a valid UUID format.
            Exception: For database connection or query execution errors.
        """
        if not self.initialized:
            await self.initialize()

        # Validate job_id format
        import uuid
        try:
            uuid.UUID(job_id)
        except ValueError as e:
            logger.error(f"Invalid UUID format for job_id: {job_id}")
            raise ValueError(f"Invalid job_id format: {job_id}") from e

        query = """
        UPDATE public.job_reviews 
        SET override_recommend = $2,
            override_comment = $3,
            override_by = $4,
            override_at = NOW(),
            updated_at = NOW()
        WHERE job_id = $1
        RETURNING id, job_id, recommend, confidence, rationale, personas, tradeoffs,
                  actions, sources, crew_output, processing_time_seconds, crew_version,
                  model_used, error_message, retry_count, created_at, updated_at,
                  override_recommend, override_comment, override_by, override_at
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    query, 
                    job_id, 
                    override_recommend, 
                    override_comment, 
                    override_by
                )
                
                if row:
                    logger.info(f"Job review override updated for job_id: {job_id}")
                    return dict(row)
                else:
                    # This is the legitimate "not found" case - job_id doesn't exist in database
                    logger.warning(f"No job review found for job_id: {job_id}")
                    return None
                    
        except Exception as e:
            # Database errors (connection, syntax, etc.) should propagate as server errors
            logger.error(f"Database error updating job review override for job_id {job_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise  # Re-raise the exception to be handled as 500 error

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
            where_conditions.append(f"COALESCE(jr.override_recommend, jr.recommend) = ${param_count}")
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
            jr.overall_alignment_score,
            jr.crew_output,
            jr.personas,
            jr.tradeoffs,
            jr.actions,
            jr.sources,
            jr.crew_version as reviewer,
            jr.created_at as review_date,
            jr.override_recommend,
            jr.override_comment,
            jr.override_by,
            jr.override_at
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
                    # Get alignment score from database column (calculated by orchestrator)
                    # Default to confidence-based calculation if not available
                    confidence_scores = {"high": 0.8, "medium": 0.6, "low": 0.4}
                    fallback_alignment_score = confidence_scores.get(row["confidence"], 0.4)
                    alignment_score = row.get("overall_alignment_score", fallback_alignment_score) or fallback_alignment_score

                    # Normalize location strings that may be null
                    raw_location = row["location"]
                    if isinstance(raw_location, str):
                        cleaned_location = raw_location.strip(", ")
                        location_value = cleaned_location if cleaned_location else None
                    else:
                        location_value = None

                    # Extract TLDR summary from crew_output JSON and keep full crew_output for dimension data
                    crew_output = self._deserialize_json_field(row.get("crew_output"))
                    tldr_summary = crew_output.get("tldr_summary") if crew_output else None

                    salary_range_formatted = self._format_salary_range(
                        row["salary_min"],
                        row["salary_max"],
                        row["salary_currency"]
                    )

                    job_data = {
                        "job": {
                            "job_id": str(row["job_id"]),
                            "title": row["title"],
                            "company": row["company"],
                            "location": location_value,
                            "url": row["url"],
                            "date_posted": row["date_posted"],
                            "source": row["source"],
                            "description": row["description"],
                            "salary_min": row["salary_min"],
                            "salary_max": row["salary_max"],
                            "salary_currency": row["salary_currency"],
                            "salary_range": salary_range_formatted,
                            "is_remote": row["is_remote"]
                        },
                        "review": {
                            "overall_alignment_score": alignment_score,
                            "recommendation": row["recommend"],
                            "confidence": row["confidence"],
                            "reviewer": row["reviewer"],
                            "review_date": row["review_date"],
                            "rationale": row["rationale"],
                            "tldr_summary": tldr_summary,
                            "crew_output": crew_output,  # Include full crew_output for dimension data
                            "personas": self._deserialize_json_field(row["personas"]),
                            "tradeoffs": self._deserialize_json_field(row["tradeoffs"]),
                            "actions": self._deserialize_json_field(row["actions"]),
                            "sources": self._deserialize_json_field(row["sources"]),
                            "override_recommend": row["override_recommend"],
                            "override_comment": row["override_comment"],
                            "override_by": row["override_by"],
                            "override_at": row["override_at"]
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

    async def get_job_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get job by URL for duplicate detection."""
        if not self.initialized:
            await self.initialize()

        query = """
        SELECT id, title, company_name, workflow_status, url
        FROM jobs
        WHERE url = $1
        LIMIT 1
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, url)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get job by URL: {str(e)}")
            return None

    async def get_job_by_normalized_fields(
        self,
        normalized_company: str,
        normalized_title: str
    ) -> Optional[Dict[str, Any]]:
        """Get job by normalized company and title for duplicate detection."""
        if not self.initialized:
            await self.initialize()

        query = """
        SELECT id, title, company_name, workflow_status, url
        FROM jobs
        WHERE normalized_company = $1 AND normalized_title = $2
        LIMIT 1
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, normalized_company, normalized_title)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get job by normalized fields: {str(e)}")
            return None

    async def get_company_by_normalized_name(self, normalized_name: str) -> Optional[Dict[str, Any]]:
        """Get company by normalized name for matching."""
        if not self.initialized:
            await self.initialize()

        query = """
        SELECT company_id, company_name, normalized_name, company_url
        FROM companies
        WHERE normalized_name = $1
        LIMIT 1
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, normalized_name)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get company by normalized name: {str(e)}")
            return None

    async def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company."""
        if not self.initialized:
            await self.initialize()

        query = """
        INSERT INTO companies (
            company_name, normalized_name, company_url, source, is_recruiting_firm, created_at
        )
        VALUES ($1, $2, $3, $4, $5, NOW())
        RETURNING company_id, company_name, normalized_name
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    company_data.get('company_name'),
                    company_data.get('normalized_name'),
                    company_data.get('company_url', ''),
                    company_data.get('source', 'manual'),
                    company_data.get('is_recruiting_firm', False)
                )
                return dict(row) if row else {}
        except Exception as e:
            logger.error(f"Failed to create company: {str(e)}")
            raise

    async def update_company(self, company_id: str, updates: Dict[str, Any]) -> bool:
        """Update company fields."""
        if not self.initialized:
            await self.initialize()

        # Build dynamic update query
        set_clauses = []
        params = []
        param_count = 1

        for key, value in updates.items():
            if key in ['mission', 'values']:
                # JSONB fields
                set_clauses.append(f"{key} = ${param_count}::jsonb")
                params.append(json.dumps(value) if not isinstance(value, str) else value)
            else:
                set_clauses.append(f"{key} = ${param_count}")
                params.append(value)
            param_count += 1

        params.append(company_id)

        query = f"""
        UPDATE companies
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE company_id = ${param_count}
        """

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, *params)
            return True
        except Exception as e:
            logger.error(f"Failed to update company: {str(e)}")
            return False

    async def insert_job(self, job_data: Dict[str, Any]) -> str:
        """Insert a new job and return job ID."""
        if not self.initialized:
            await self.initialize()

        query = """
        INSERT INTO jobs (
            title, company_id, company_name, location, description, url,
            source, workflow_status, date_posted, salary_min, salary_max,
            scraped_at, normalized_title, normalized_company, created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, NOW())
        RETURNING id
        """

        try:
            async with self.pool.acquire() as conn:
                job_id = await conn.fetchval(
                    query,
                    job_data.get('title'),
                    job_data.get('company_id'),
                    job_data.get('company_name'),
                    job_data.get('location'),
                    job_data.get('description'),
                    job_data.get('url'),
                    job_data.get('source', 'manual'),
                    job_data.get('workflow_status', 'pending_review'),
                    job_data.get('date_posted'),
                    job_data.get('salary_min'),
                    job_data.get('salary_max'),
                    job_data.get('scraped_at'),
                    job_data.get('normalized_title'),
                    job_data.get('normalized_company')
                )
                return str(job_id)
        except Exception as e:
            logger.error(f"Failed to insert job: {str(e)}")
            raise

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        if not self.initialized:
            await self.initialize()

        query = """
        SELECT *
        FROM jobs
        WHERE id = $1
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, job_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get job: {str(e)}")
            return None

    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job fields."""
        if not self.initialized:
            await self.initialize()

        # Build dynamic update query
        set_clauses = []
        params = []
        param_count = 1

        for key, value in updates.items():
            set_clauses.append(f"{key} = ${param_count}")
            params.append(value)
            param_count += 1

        params.append(job_id)

        query = f"""
        UPDATE jobs
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${param_count}
        """

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, *params)
            return True
        except Exception as e:
            logger.error(f"Failed to update job: {str(e)}")
            return False


def get_database_service() -> DatabaseService:
    """Create a new database service instance."""
    return DatabaseService()
