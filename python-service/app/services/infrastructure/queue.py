"""
Queue service for managing RQ job queuing and execution.
"""
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis
from rq import Queue, Worker, Connection
from loguru import logger

from ...core.config import get_settings
from .database import get_database_service
from .worker import scrape_jobs_worker, process_job_review, run_linkedin_job_search


class QueueService:
    """Service for managing job queues with RQ."""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_conn: Optional[redis.Redis] = None
        self.queue: Optional[Queue] = None  # Main scraping queue
        self.review_queue: Optional[Queue] = None  # Job review queue
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize Redis connection and queue."""
        try:
            self.redis_conn = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=self.settings.redis_db,
            )
            
            # Test connection
            self.redis_conn.ping()
            
            self.queue = Queue(
                name=self.settings.rq_queue_name,
                connection=self.redis_conn,
                default_timeout=self.settings.rq_job_timeout
            )
            
            # Create job review queue
            self.review_queue = Queue(
                name=self.settings.job_review_queue_name,
                connection=self.redis_conn,
                default_timeout=self.settings.rq_job_timeout
            )
            
            self.initialized = True
            logger.info(f"Queue service initialized - Scraping queue: {self.settings.rq_queue_name}, Review queue: {self.settings.job_review_queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize queue service: {str(e)}")
            return False

    def enqueue_scraping_job(self, 
                           payload: Dict[str, Any],
                           site_schedule_id: Optional[str] = None,
                           trigger: str = "manual",
                           run_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Enqueue a job scraping task.
        
        Args:
            payload: Job search parameters
            site_schedule_id: Site schedule ID for scheduled jobs
            trigger: 'manual' or 'schedule'  
            run_id: Optional custom run ID
            
        Returns:
            Dictionary with task_id and run_id, or None if failed
        """
        if not self.initialized:
            logger.error("Queue service not initialized")
            return None
        
        try:
            # Generate run_id if not provided
            if not run_id:
                run_id = f"run_{uuid.uuid4().hex[:8]}"
            
            # Get pause settings from site schedule if available
            min_pause = 2
            max_pause = 8
            max_retries = 3
            
            if site_schedule_id:
                # TODO: Get these from site_schedules table
                # For now, use defaults
                pass
            
            # Enqueue the job
            job = self.queue.enqueue(
                scrape_jobs_worker,
                site_schedule_id=site_schedule_id,
                payload=payload,
                run_id=run_id,
                min_pause=min_pause,
                max_pause=max_pause,
                max_retries=max_retries,
                job_id=run_id,  # Use run_id as job_id for consistency
                result_ttl=self.settings.rq_result_ttl
            )
            
            logger.info(f"Enqueued job - run_id: {run_id}, task_id: {job.id}, trigger: {trigger}")
            
            return {
                "task_id": job.id,
                "run_id": run_id
            }
            
        except Exception as e:
            logger.error(f"Failed to enqueue scraping job: {str(e)}")
            return None

    def enqueue_job_review(self, job_id: str, max_retries: int = 3) -> Optional[str]:
        """
        Enqueue a job for review processing.
        
        Args:
            job_id: UUID of the job to review
            max_retries: Maximum number of retry attempts
            
        Returns:
            Task ID if successful, None if failed
        """
        if not self.initialized:
            logger.error("Queue service not initialized")
            return None
            
        try:
            job = self.review_queue.enqueue(
                process_job_review,
                job_id,
                max_retries,
                job_timeout=self.settings.rq_job_timeout,
                result_ttl=self.settings.rq_result_ttl
            )
            
            logger.info(f"Enqueued job review - job_id: {job_id}, task_id: {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to enqueue job review for {job_id}: {str(e)}")
            return None

    def enqueue_multiple_job_reviews(self, job_ids: List[str], max_retries: int = 3) -> Dict[str, Optional[str]]:
        """
        Enqueue multiple jobs for review processing.
        
        Args:
            job_ids: List of job UUIDs to review
            max_retries: Maximum number of retry attempts per job
            
        Returns:
            Dictionary mapping job_id to task_id (or None if failed)
        """
        if not self.initialized:
            logger.error("Queue service not initialized")
            return {}
        
        results = {}
        for job_id in job_ids:
            task_id = self.enqueue_job_review(job_id, max_retries)
            results[job_id] = task_id
            
        successful = sum(1 for task_id in results.values() if task_id is not None)
        logger.info(f"Enqueued {successful}/{len(job_ids)} job reviews successfully")
        return results

    def enqueue_linkedin_job_search(self, 
                                   payload: Dict[str, Any],
                                   site_schedule_id: Optional[str] = None,
                                   trigger: str = "manual",
                                   run_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Enqueue a LinkedIn job search task.
        
        Args:
            payload: LinkedIn job search parameters
            site_schedule_id: Site schedule ID for scheduled jobs
            trigger: 'manual' or 'schedule'  
            run_id: Optional custom run ID
            
        Returns:
            Dictionary with task_id and run_id, or None if failed
        """
        if not self.initialized:
            logger.error("Queue service not initialized")
            return None
        
        try:
            # Generate run_id if not provided
            if not run_id:
                run_id = f"linkedin_run_{uuid.uuid4().hex[:8]}"
            
            # Get retry settings from site schedule if available
            max_retries = 3
            
            if site_schedule_id:
                # TODO: Get these from site_schedules table
                # For now, use defaults
                pass
            
            # Enqueue the LinkedIn job search
            job = self.queue.enqueue(
                run_linkedin_job_search,
                site_schedule_id=site_schedule_id,
                payload=payload,
                run_id=run_id,
                max_retries=max_retries,
                job_id=run_id,  # Use run_id as job_id for consistency
                result_ttl=self.settings.rq_result_ttl
            )
            
            logger.info(f"Enqueued LinkedIn job search - run_id: {run_id}, task_id: {job.id}, trigger: {trigger}")
            
            return {
                "task_id": job.id,
                "run_id": run_id
            }
            
        except Exception as e:
            logger.error(f"Failed to enqueue LinkedIn job search: {str(e)}")
            return None

    def get_job_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a queued job."""
        if not self.initialized:
            return None
        
        try:
            from rq.job import Job
            job = Job.fetch(task_id, connection=self.redis_conn)
            
            return {
                "task_id": task_id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "result": job.result if job.is_finished else None,
                "exc_info": job.exc_info if job.is_failed else None
            }
        except Exception as e:
            logger.error(f"Failed to get job status for {task_id}: {str(e)}")
            return None

    def get_queue_info(self, queue_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about the queue(s)."""
        if not self.initialized:
            return {}
        
        try:
            if queue_name == "review" or queue_name == self.settings.job_review_queue_name:
                # Return review queue info
                return {
                    "name": self.review_queue.name,
                    "length": len(self.review_queue),
                    "started_jobs": self.review_queue.started_job_registry.count,
                    "finished_jobs": self.review_queue.finished_job_registry.count,
                    "failed_jobs": self.review_queue.failed_job_registry.count,
                    "deferred_jobs": self.review_queue.deferred_job_registry.count
                }
            elif queue_name == "scraping" or queue_name == self.settings.rq_queue_name:
                # Return scraping queue info
                return {
                    "name": self.queue.name,
                    "length": len(self.queue),
                    "started_jobs": self.queue.started_job_registry.count,
                    "finished_jobs": self.queue.finished_job_registry.count,
                    "failed_jobs": self.queue.failed_job_registry.count,
                    "deferred_jobs": self.queue.deferred_job_registry.count
                }
            else:
                # Return info for both queues
                return {
                    "scraping_queue": {
                        "name": self.queue.name,
                        "length": len(self.queue),
                        "started_jobs": self.queue.started_job_registry.count,
                        "finished_jobs": self.queue.finished_job_registry.count,
                        "failed_jobs": self.queue.failed_job_registry.count,
                        "deferred_jobs": self.queue.deferred_job_registry.count
                    },
                    "review_queue": {
                        "name": self.review_queue.name,
                        "length": len(self.review_queue),
                        "started_jobs": self.review_queue.started_job_registry.count,
                        "finished_jobs": self.review_queue.finished_job_registry.count,
                        "failed_jobs": self.review_queue.failed_job_registry.count,
                        "deferred_jobs": self.review_queue.deferred_job_registry.count
                    }
                }
        except Exception as e:
            logger.error(f"Failed to get queue info: {str(e)}")
            return {}

    def check_redis_lock(self, key: str, timeout: int = 30) -> Optional[Any]:
        """Check if a Redis lock exists for the given key."""
        if not self.initialized:
            return None
        
        try:
            return self.redis_conn.get(key)
        except Exception as e:
            logger.error(f"Failed to check Redis lock for {key}: {str(e)}")
            return None

    def acquire_redis_lock(self, key: str, value: str, timeout: int = 300) -> bool:
        """Acquire a Redis lock for the given key."""
        if not self.initialized:
            return False

        try:
            # Use SET with NX (only if not exists) and EX (expiry)
            result = self.redis_conn.set(key, value, nx=True, ex=timeout)
            return result is True
        except Exception as e:
            logger.error(f"Failed to acquire Redis lock for {key}: {str(e)}")
            return False

    def enqueue_with_site_lock(self,
                              payload: Dict[str, Any],
                              site_name: str,
                              site_schedule_id: Optional[str] = None,
                              trigger: str = "manual",
                              run_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Enqueue a scraping job only if no other job is running for the same site.
        This prevents overlapping scrapes per site which cause bot blocks.

        Args:
            payload: Job search parameters
            site_name: The site being scraped (for locking)
            site_schedule_id: Site schedule ID
            trigger: 'manual' or 'schedule'
            run_id: Optional custom run ID

        Returns:
            Dictionary with task_id and run_id, or None if site busy
        """
        if not self.initialized:
            logger.warning("Queue service not initialized, cannot enqueue with site lock")
            return None

        lock_key = f"site_active_job:{site_name}"

        try:
            # Check if site already has an active job
            existing_active_job = self.check_redis_lock(lock_key)
            if existing_active_job:
                logger.info(f"Site {site_name} already has active job, queuing denied: {existing_active_job.decode('utf-8')}")
                return None  # Site busy, don't queue

            # Generate run_id if not provided
            if not run_id:
                run_id = f"site_lock_{uuid.uuid4().hex[:8]}"

            # Acquire site-level lock
            lock_value = f"{run_id}:{datetime.now().isoformat()}"
            if not self.acquire_redis_lock(lock_key, lock_value, timeout=3600):  # 1 hour timeout
                logger.warning(f"Failed to acquire site lock for {site_name}")
                return None

            # Lock acquired, now enqueue the job
            job_info = self.enqueue_scraping_job(
                payload=payload,
                site_schedule_id=site_schedule_id,
                trigger=trigger,
                run_id=run_id
            )

            if not job_info:
                # Failed to enqueue, release the lock
                self.release_redis_lock(lock_key, lock_value)
                logger.error(f"Failed to enqueue job after acquiring lock for {site_name}")
                return None

            logger.info(f"Successfully enqueued locked job for {site_name} - run_id: {run_id}")
            return job_info

        except Exception as e:
            logger.error(f"Error in site-locked enqueue for {site_name}: {str(e)}")
            return None

    def enqueue_linkedin_with_site_lock(self,
                                       payload: Dict[str, Any],
                                       site_schedule_id: Optional[str] = None,
                                       trigger: str = "manual",
                                       run_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Enqueue LinkedIn job search with site-level locking.

        Args:
            payload: LinkedIn job search parameters
            site_schedule_id: Site schedule ID
            trigger: 'manual' or 'schedule'
            run_id: Optional custom run ID

        Returns:
            Dictionary with task_id and run_id, or None if site busy
        """
        return self.enqueue_with_site_lock(
            payload=payload,
            site_name="linkedin",
            site_schedule_id=site_schedule_id,
            trigger=trigger,
            run_id=run_id
        )

    def release_redis_lock(self, key: str, value: str) -> bool:
        """Release a Redis lock if we own it."""
        if not self.initialized:
            return False

        try:
            # Lua script to atomically check and delete
            lua_script = """
            if redis.call("GET", KEYS[1]) == ARGV[1] then
                return redis.call("DEL", KEYS[1])
            else
                return 0
            end
            """
            result = self.redis_conn.eval(lua_script, 1, key, value)
            return result == 1
        except Exception as e:
            logger.error(f"Failed to release Redis lock for {key}: {str(e)}")
            return False


    def clear_orphaned_locks(self, pattern: str = "scrape_lock:*", max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clear orphaned Redis locks that don't have corresponding active jobs.

        Args:
            pattern: Redis key pattern for locks to check (default: scrape locks)
            max_age_hours: Maximum age for locks to consider (older = orphaned)

        Returns:
            Dictionary with cleanup results
        """
        if not self.initialized:
            logger.warning("Queue service not initialized, cannot clear orphaned locks")
            return {"error": "Queue service not initialized"}

        try:
            import time
            from rq.job import Job

            cleared = []
            skipped = []
            errors = []
            current_time = time.time()

            # Get all keys matching the pattern
            lock_keys = self.redis_conn.keys(pattern)
            logger.info(f"Found {len(lock_keys)} lock keys matching pattern '{pattern}'")

            for lock_key_bytes in lock_keys:
                lock_key = lock_key_bytes.decode('utf-8')

                try:
                    lock_value = self.redis_conn.get(lock_key)
                    if not lock_value:
                        # Key exists but no value - should be cleared
                        self.redis_conn.delete(lock_key)
                        cleared.append({"key": lock_key, "reason": "empty_value"})
                        continue

                    lock_value_str = lock_value.decode('utf-8')
                    logger.debug(f"Checking lock {lock_key} with value {lock_value_str}")

                    # Parse lock value format: "run_id:timestamp"
                    if ":" not in lock_value_str:
                        logger.warning(f"Invalid lock value format for {lock_key}: {lock_value_str}")
                        continue

                    run_id, timestamp_str = lock_value_str.split(":", 1)

                    # Check if it's an old lock (older than max_age_hours)
                    try:
                        import datetime
                        from datetime import timezone
                        lock_time = datetime.datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
                        age_hours = (datetime.datetime.now(timezone.utc) - lock_time).total_seconds() / 3600

                        if age_hours > max_age_hours:
                            logger.info(f"Clearing old lock {lock_key} (age: {age_hours:.1f} hours)")
                            self.redis_conn.delete(lock_key)
                            cleared.append({"key": lock_key, "reason": f"too_old_{age_hours:.1f}h", "run_id": run_id})
                            continue
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Could not parse timestamp for lock {lock_key}: {timestamp_str}")
                        # Continue with job checking...

                    # Check if there's an active job for this run_id
                    try:
                        job = Job.fetch(run_id, connection=self.redis_conn)
                        if job and (job.is_started or job.is_queued):
                            skipped.append({"key": lock_key, "reason": "active_job", "run_id": run_id})
                            logger.debug(f"Skipping lock {lock_key} - active job {run_id}")
                            continue
                    except Exception:
                        # Job doesn't exist or fetch failed - lock is orphaned
                        pass

                    # Lock has no active job - orphan
                    logger.info(f"Clearing orphaned lock {lock_key} (run_id: {run_id})")
                    self.redis_conn.delete(lock_key)
                    cleared.append({"key": lock_key, "reason": "orphaned", "run_id": run_id})

                except Exception as e:
                    error_msg = f"Error processing lock {lock_key}: {str(e)}"
                    logger.error(error_msg)
                    errors.append({"key": lock_key, "error": error_msg})

            result = {
                "pattern_checked": pattern,
                "locks_cleared": len(cleared),
                "locks_skipped": len(skipped),
                "errors_count": len(errors),
                "cleared_details": cleared,
                "skipped_details": skipped[:10],  # Limit for readability
                "errors": errors
            }

            logger.info(f"Orphaned lock cleanup complete: {len(cleared)} cleared, {len(skipped)} skipped, {len(errors)} errors")
            return result

        except Exception as e:
            error_msg = f"Failed to clear orphaned locks: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}


def get_queue_service() -> QueueService:
    """Create a new queue service instance."""
    return QueueService()
