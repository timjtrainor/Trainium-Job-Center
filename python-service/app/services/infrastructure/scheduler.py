"""
Scheduler service for managing periodic job scraping tasks.
"""
import uuid
import random
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from loguru import logger

from .database import get_database_service
from .queue import get_queue_service


class SchedulerService:
    """Service for scheduling periodic job scraping tasks."""

    def __init__(self):
        self.db_service = get_database_service()
        self.queue_service = get_queue_service()
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize scheduler dependencies."""
        try:
            db_init = await self.db_service.initialize()
            queue_init = await self.queue_service.initialize()

            self.initialized = db_init and queue_init

            if self.initialized:
                logger.info("Scheduler service initialized successfully")
            else:
                logger.error("Failed to initialize scheduler dependencies")

            return self.initialized
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {str(e)}")
            return False

    async def process_scheduled_sites(self) -> int:
        """
        Process all enabled site schedules that are due for execution.

        Returns:
            Number of jobs enqueued
        """
        if not self.initialized:
            logger.warning("Scheduler not initialized")
            return 0

        try:
            # Get all enabled sites that are due
            schedules = await self.db_service.get_enabled_site_schedules()
            jobs_enqueued = 0

            logger.info(f"Found {len(schedules)} site schedules to process")

            for schedule in schedules:
                lock_key: Optional[str] = None
                lock_value: Optional[str] = None
                run_id: Optional[str] = None
                lock_acquired = False

                try:
                    site_name = schedule["site_name"]
                    schedule_id = str(schedule["id"])

                    # Check for existing running jobs for this site (per-site lock)
                    lock_key = f"scrape_lock:{site_name}"
                    existing_lock = self.queue_service.check_redis_lock(lock_key)

                    if existing_lock:
                        logger.info(f"Site {site_name} is already being scraped, skipping")
                        continue

                    # Check database for running jobs as backup
                    if await self.db_service.check_site_lock(site_name):
                        logger.info(f"Site {site_name} has running jobs in database, skipping")
                        continue

                    # Generate unique run ID
                    run_id = f"sched_{uuid.uuid4().hex[:8]}"

                    # Acquire Redis lock for this site
                    lock_value = f"{run_id}:{datetime.now(timezone.utc).isoformat()}"
                    if not self.queue_service.acquire_redis_lock(lock_key, lock_value, timeout=1800):  # 30 min timeout
                        logger.warning(f"Failed to acquire lock for site {site_name}")
                        continue

                    lock_acquired = True

                    # Enqueue the job with site name included in payload
                    payload_dict = schedule["payload"]
                    if isinstance(payload_dict, str):
                        try:
                            payload_dict = json.loads(payload_dict)
                        except json.JSONDecodeError as json_err:
                            logger.error(f"Failed to parse payload JSON for {site_name}: {json_err}")
                            if lock_acquired and lock_key and lock_value:
                                self.queue_service.release_redis_lock(lock_key, lock_value)
                                lock_acquired = False
                                lock_value = None
                            continue

                    # Ensure payload_dict is a dictionary
                    if not isinstance(payload_dict, dict):
                        logger.error(f"Payload is not a dictionary for {site_name}: {type(payload_dict)}")
                        if lock_acquired and lock_key and lock_value:
                            self.queue_service.release_redis_lock(lock_key, lock_value)
                            lock_acquired = False
                            lock_value = None
                        continue

                    payload = {**payload_dict, "site_name": schedule["site_name"]}
                    task_type = (payload_dict or {}).get("task_type", "scrape").lower()

                    job_info: Optional[Dict[str, str]] = None

                    if task_type == "resume_tailoring":
                        reference_id = payload_dict.get("application_id")
                        await self.db_service.create_ai_task_run(
                            run_id=run_id,
                            task_type="resume_tailoring",
                            trigger="schedule",
                            reference_id=reference_id,
                            schedule_id=schedule_id,
                            payload=payload_dict,
                        )
                        job_info = self.queue_service.enqueue_resume_tailoring_job(
                            application_id=reference_id,
                            payload=payload_dict,
                            run_id=run_id,
                            trigger="schedule",
                            schedule_id=schedule_id,
                        )
                    elif task_type == "company_research":
                        reference_id = payload_dict.get("company_id")
                        await self.db_service.create_ai_task_run(
                            run_id=run_id,
                            task_type="company_research",
                            trigger="schedule",
                            reference_id=reference_id,
                            schedule_id=schedule_id,
                            payload=payload_dict,
                        )
                        job_info = self.queue_service.enqueue_company_research_job(
                            company_id=reference_id,
                            payload=payload_dict,
                            run_id=run_id,
                            trigger="schedule",
                            schedule_id=schedule_id,
                        )
                    else:
                        scrape_run_id = await self.db_service.create_scrape_run(
                            run_id=run_id,
                            site_schedule_id=schedule_id,
                            task_id="",
                            trigger="schedule",
                        )

                        if not scrape_run_id:
                            logger.error(f"Failed to create scrape run record for {site_name}")
                            continue

                        if site_name.lower() == "linkedin":
                            job_info = self.queue_service.enqueue_linkedin_with_site_lock(
                                payload=payload,
                                site_schedule_id=schedule_id,
                                trigger="schedule",
                                run_id=run_id
                            )
                        else:
                            job_info = self.queue_service.enqueue_with_site_lock(
                                payload=payload,
                                site_name=site_name,
                                site_schedule_id=schedule_id,
                                trigger="schedule",
                                run_id=run_id
                            )

                    if job_info:
                        task_id = job_info["task_id"]

                        if task_type in {"resume_tailoring", "company_research"}:
                            await self.db_service.update_ai_task_run(
                                run_id,
                                status="queued",
                                task_id=task_id,
                            )
                        else:
                            await self.db_service.update_scrape_run_status(
                                run_id=run_id,
                                status="queued",
                                task_id=task_id,
                                message=f"Scheduled scrape for {site_name}"
                            )

                        # Calculate next run time with jitter
                        interval_minutes = schedule["interval_minutes"]
                        jitter_percent = random.uniform(-0.1, 0.1)  # ±10% jitter
                        jittered_minutes = interval_minutes * (1 + jitter_percent)
                        next_run_at = datetime.now(timezone.utc) + timedelta(minutes=jittered_minutes)

                        # Update schedule next run time
                        await self.db_service.update_site_schedule_next_run(schedule_id, next_run_at)

                        logger.info(
                            "Enqueued scheduled job",
                            site_name=site_name,
                            task_type=task_type,
                            run_id=run_id,
                            task_id=task_id,
                            next_run=next_run_at.isoformat(),
                        )

                        jobs_enqueued += 1

                        # Release the lock - the worker will manage its own execution
                        # The lock was just to prevent duplicate scheduling
                        if lock_acquired and lock_key and lock_value:
                            self.queue_service.release_redis_lock(lock_key, lock_value)
                            lock_acquired = False
                            lock_value = None
                    else:
                        logger.error(f"Failed to enqueue job for {site_name}")

                        if run_id:
                            if task_type in {"resume_tailoring", "company_research"}:
                                await self.db_service.update_ai_task_run(
                                    run_id,
                                    status="failed",
                                    error="Failed to enqueue job",
                                )
                            else:
                                await self.db_service.update_scrape_run_status(
                                    run_id=run_id,
                                    status="failed",
                                    message="Failed to enqueue job"
                                )

                        if lock_acquired and lock_key and lock_value:
                            self.queue_service.release_redis_lock(lock_key, lock_value)
                            lock_acquired = False
                            lock_value = None

                except Exception as e:
                    site_name = "unknown"
                    try:
                        if isinstance(schedule, dict):
                            site_name = schedule.get('site_name', 'unknown')
                        else:
                            site_name = f"invalid_schedule_type_{type(schedule).__name__}"
                    except Exception:
                        pass  # Keep default site_name if we can't extract it

                    logger.error(f"Error processing schedule for {site_name}: {str(e)}")

                    if run_id:
                        try:
                            await self.db_service.update_scrape_run_status(
                                run_id=run_id,
                                status="failed",
                                message=f"Scheduler error for {site_name}: {str(e)}"
                            )
                        except Exception as update_err:
                            logger.error(f"Failed to mark scrape run {run_id} as failed: {update_err}")

                    if lock_acquired and lock_key and lock_value:
                        self.queue_service.release_redis_lock(lock_key, lock_value)
                        lock_acquired = False
                        lock_value = None

                    continue

                finally:
                    if lock_acquired and lock_key and lock_value:
                        self.queue_service.release_redis_lock(lock_key, lock_value)
                        lock_acquired = False
                        lock_value = None

            if jobs_enqueued > 0:
                logger.info(f"Scheduler enqueued {jobs_enqueued} jobs")

            return jobs_enqueued

        except Exception as e:
            logger.error(f"Error in process_scheduled_sites: {str(e)}")
            return 0

    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get status information about the scheduler."""
        try:
            if not self.initialized:
                return {"status": "not_initialized", "error": "Scheduler not initialized"}

            # Get queue info
            queue_info = self.queue_service.get_queue_info()

            # Get enabled schedules count
            schedules = await self.db_service.get_enabled_site_schedules()

            return {
                "status": "running",
                "enabled_sites": len(schedules),
                "queue_info": queue_info,
                "last_check": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return {"status": "error", "error": str(e)}


def get_scheduler_service() -> SchedulerService:
    """Create a new scheduler service instance."""
    return SchedulerService()
