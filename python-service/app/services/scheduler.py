"""
Scheduler service for managing periodic job scraping tasks.
"""
import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
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
                    
                    # Create scrape run record
                    scrape_run_id = await self.db_service.create_scrape_run(
                        run_id=run_id,
                        site_schedule_id=schedule_id,
                        task_id="",  # Will be updated after enqueueing
                        trigger="schedule"
                    )
                    
                    if not scrape_run_id:
                        logger.error(f"Failed to create scrape run record for {site_name}")
                        self.queue_service.release_redis_lock(lock_key, lock_value)
                        continue
                    
                    # Enqueue the job with site name included in payload
                    payload = {**schedule["payload"], "site_name": schedule["site_name"]}
                    job_info = self.queue_service.enqueue_scraping_job(
                        payload=payload,
                        site_schedule_id=schedule_id,
                        trigger="schedule",
                        run_id=run_id
                    )
                    
                    if job_info:
                        task_id = job_info["task_id"]
                        
                        # Update scrape run with task_id
                        await self.db_service.update_scrape_run_status(
                            run_id=run_id,
                            status="queued",
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
                            f"Enqueued scheduled job for {site_name} - "
                            f"run_id: {run_id}, task_id: {task_id}, "
                            f"next_run: {next_run_at.isoformat()}"
                        )
                        
                        jobs_enqueued += 1
                        
                        # Release the lock - the worker will manage its own execution
                        # The lock was just to prevent duplicate scheduling
                        self.queue_service.release_redis_lock(lock_key, lock_value)
                    else:
                        logger.error(f"Failed to enqueue job for {site_name}")
                        self.queue_service.release_redis_lock(lock_key, lock_value)
                        
                        # Update scrape run to failed
                        await self.db_service.update_scrape_run_status(
                            run_id=run_id,
                            status="failed",
                            message="Failed to enqueue job"
                        )
                        
                except Exception as e:
                    logger.error(f"Error processing schedule for {schedule.get('site_name', 'unknown')}: {str(e)}")
                    continue
            
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


# Global instance
_scheduler_service: Optional[SchedulerService] = None

def get_scheduler_service() -> SchedulerService:
    """Get or create the global scheduler service instance."""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service