"""
Scheduler service for managing periodic job scraping tasks.
"""
import uuid
import random
import json
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
        Enhanced with comprehensive logging and reliability improvements.
        
        Returns:
            Number of jobs enqueued
        """
        if not self.initialized:
            logger.warning("Scheduler not initialized")
            return 0
        
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting scheduler check at {start_time.isoformat()}")
        
        try:
            # Get all enabled sites that are due
            schedules = await self.db_service.get_enabled_site_schedules()
            jobs_enqueued = 0
            
            logger.info(f"Found {len(schedules)} site schedules to process")
            
            if len(schedules) == 0:
                logger.info("No enabled site schedules found or none are due for execution")
                return 0
            
            # Log schedule details for diagnostics
            for i, schedule in enumerate(schedules):
                site_name = schedule.get("site_name", "unknown")
                next_run = schedule.get("next_run_at")
                last_run = schedule.get("last_run_at")
                interval = schedule.get("interval_minutes", "unknown")
                
                logger.info(
                    f"Schedule {i+1}/{len(schedules)}: {site_name} - "
                    f"interval: {interval}min, "
                    f"last_run: {last_run}, "
                    f"next_run: {next_run}"
                )
            
            for schedule in schedules:
                try:
                    site_name = schedule["site_name"]
                    schedule_id = str(schedule["id"])
                    
                    logger.info(f"Processing schedule for site: {site_name} (ID: {schedule_id})")
                    
                    # Check for existing running jobs for this site (per-site lock)
                    lock_key = f"scrape_lock:{site_name}"
                    existing_lock = self.queue_service.check_redis_lock(lock_key)
                    
                    if existing_lock:
                        logger.info(f"Site {site_name} is already being scraped (Redis lock exists), skipping")
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
                        logger.warning(f"Failed to acquire Redis lock for site {site_name}")
                        continue
                    
                    logger.info(f"Acquired Redis lock for {site_name}: {lock_key}")
                    
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
                    
                    logger.info(f"Created scrape run record: {scrape_run_id} for run_id: {run_id}")
                    
                    # Parse and validate payload
                    payload_dict = schedule["payload"]
                    if isinstance(payload_dict, str):
                        try:
                            payload_dict = json.loads(payload_dict)
                        except json.JSONDecodeError as json_err:
                            logger.error(f"Failed to parse payload JSON for {site_name}: {json_err}")
                            self.queue_service.release_redis_lock(lock_key, lock_value)
                            continue
                    
                    # Ensure payload_dict is a dictionary
                    if not isinstance(payload_dict, dict):
                        logger.error(f"Payload is not a dictionary for {site_name}: {type(payload_dict)}")
                        self.queue_service.release_redis_lock(lock_key, lock_value)
                        continue

                    # Add pagination configuration to payload if not present
                    payload = {**payload_dict, "site_name": schedule["site_name"]}
                    
                    # Auto-enable pagination for high result counts
                    results_wanted = payload.get("results_wanted", 15)
                    if results_wanted > 25:
                        payload["enable_pagination"] = True
                        payload["max_results_target"] = results_wanted
                        logger.info(f"Auto-enabled pagination for {site_name} - target: {results_wanted} results")
                    elif payload.get("enable_pagination", False):
                        # Explicit pagination enabled, ensure max_results_target is set
                        if "max_results_target" not in payload:
                            payload["max_results_target"] = results_wanted
                        logger.info(f"Explicit pagination enabled for {site_name} - target: {payload['max_results_target']} results")
                    
                    logger.info(f"Enqueuing scrape job for {site_name} with payload keys: {list(payload.keys())}")
                    
                    # Enqueue the job with site name included in payload
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
                            f"✅ Successfully enqueued scheduled job for {site_name} - "
                            f"run_id: {run_id}, task_id: {task_id}, "
                            f"next_run: {next_run_at.isoformat()}"
                        )
                        
                        jobs_enqueued += 1
                        
                        # Release the lock - the worker will manage its own execution
                        # The lock was just to prevent duplicate scheduling
                        self.queue_service.release_redis_lock(lock_key, lock_value)
                        logger.debug(f"Released Redis lock for {site_name}")
                    else:
                        logger.error(f"❌ Failed to enqueue job for {site_name}")
                        self.queue_service.release_redis_lock(lock_key, lock_value)
                        
                        # Update scrape run to failed
                        await self.db_service.update_scrape_run_status(
                            run_id=run_id,
                            status="failed",
                            message="Failed to enqueue job"
                        )
                        
                except Exception as e:
                    site_name = "unknown"
                    try:
                        if isinstance(schedule, dict):
                            site_name = schedule.get('site_name', 'unknown')
                        else:
                            site_name = f"invalid_schedule_type_{type(schedule).__name__}"
                    except:
                        pass  # Keep default site_name if we can't extract it
                    logger.error(f"❌ Error processing schedule for {site_name}: {str(e)}")
                    continue
            
            # Final summary logging
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            if jobs_enqueued > 0:
                logger.info(f"🎉 Scheduler completed successfully - enqueued {jobs_enqueued} jobs in {duration:.2f}s")
            else:
                logger.info(f"⏸️ Scheduler completed - no jobs enqueued (duration: {duration:.2f}s)")
            
            return jobs_enqueued
            
        except Exception as e:
            logger.error(f"💥 Critical error in process_scheduled_sites: {str(e)}")
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
