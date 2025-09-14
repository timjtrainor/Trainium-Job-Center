"""
Queue service for managing RQ job queuing and execution.
"""
import uuid
from typing import Dict, Any, Optional, List
import redis
from rq import Queue, Worker, Connection
from loguru import logger

from ...core.config import get_settings
from .database import get_database_service
from .worker import scrape_jobs_worker, process_job_review


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

    def enqueue_job_review(self, job_data: Dict[str, Any]) -> Optional[str]:
        """
        Enqueue a job for review processing.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Task ID if successful, None if failed
        """
        if not self.initialized:
            logger.error("Queue service not initialized")
            return None
            
        try:
            job = self.review_queue.enqueue(
                process_job_review,
                job_data,
                job_timeout=self.settings.rq_job_timeout,
                result_ttl=self.settings.rq_result_ttl
            )
            
            logger.info(f"Enqueued job review - job_id: {job_data.get('job_id')}, task_id: {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Failed to enqueue job review: {str(e)}")
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

    def get_queue_info(self) -> Dict[str, Any]:
        """Get information about the queue."""
        if not self.initialized:
            return {}
        
        try:
            return {
                "name": self.queue.name,
                "length": len(self.queue),
                "started_jobs": self.queue.started_job_registry.count,
                "finished_jobs": self.queue.finished_job_registry.count,
                "failed_jobs": self.queue.failed_job_registry.count,
                "deferred_jobs": self.queue.deferred_job_registry.count
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


def get_queue_service() -> QueueService:
    """Create a new queue service instance."""
    return QueueService()

