"""
Job Review Service for managing job review workflow.

This service provides high-level operations for:
- Queuing jobs for review
- Processing batches of pending jobs  
- Checking review status
- Managing retry logic
"""
import asyncio
from typing import Dict, List, Optional, Any
from loguru import logger

from .database import get_database_service

from ...core.config import get_settings


class JobReviewService:
    """Service for managing job review operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_service = get_database_service()
        from .queue import get_queue_service
        self.queue_service = get_queue_service()
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the service."""
        try:
            # Initialize database service
            if not self.db_service.initialized:
                await self.db_service.initialize()
            
            # Initialize queue service  
            if not self.queue_service.initialized:
                await self.queue_service.initialize()
            
            self.initialized = True
            logger.info("Job Review Service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Job Review Service: {e}")
            return False
    
    async def queue_pending_jobs(self, limit: int = 50, max_retries: int = 3) -> Dict[str, Any]:
        """
        Find pending review jobs and queue them for processing.
        
        Args:
            limit: Maximum number of jobs to queue
            max_retries: Maximum retry attempts per job
            
        Returns:
            Summary of queuing operation
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get pending jobs
            pending_jobs = await self.db_service.get_pending_review_jobs(limit)
            
            if not pending_jobs:
                logger.info("No pending review jobs found")
                return {
                    "status": "success",
                    "queued_count": 0,
                    "failed_count": 0,
                    "message": "No pending jobs to queue"
                }
            
            logger.info(f"Found {len(pending_jobs)} jobs pending review")
            
            # Extract job IDs
            job_ids = [str(job["id"]) for job in pending_jobs]
            
            # Queue jobs for review
            results = self.queue_service.enqueue_multiple_job_reviews(job_ids, max_retries)
            
            # Count successes and failures
            queued_count = sum(1 for task_id in results.values() if task_id is not None)
            failed_count = len(results) - queued_count
            
            # Log failures
            if failed_count > 0:
                failed_jobs = [job_id for job_id, task_id in results.items() if task_id is None]
                logger.warning(f"Failed to queue {failed_count} jobs: {failed_jobs}")
            
            return {
                "status": "success",
                "queued_count": queued_count,
                "failed_count": failed_count,
                "message": f"Queued {queued_count}/{len(pending_jobs)} jobs for review",
                "task_mapping": results
            }
            
        except Exception as e:
            error_msg = f"Failed to queue pending jobs: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "queued_count": 0,
                "failed_count": 0,
                "message": error_msg
            }
    
    async def get_review_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the review status for a specific job.
        
        Args:
            job_id: UUID of the job
            
        Returns:
            Review status information or None if not found
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get job info
            job = await self.db_service.get_job_by_id(job_id)
            if not job:
                return None
            
            # Get review info if it exists
            review = await self.db_service.get_job_review(job_id)
            
            return {
                "job_id": job_id,
                "job_title": job.get("title"),
                "job_company": job.get("company"),
                "job_status": job.get("status"),
                "review_exists": review is not None,
                "review_data": {
                    "recommend": review.get("recommend"),
                    "confidence": review.get("confidence"),
                    "rationale": review.get("rationale"),
                    "retry_count": review.get("retry_count"),
                    "error_message": review.get("error_message"),
                    "created_at": review.get("created_at").isoformat() if review.get("created_at") else None,
                    "updated_at": review.get("updated_at").isoformat() if review.get("updated_at") else None,
                } if review else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get review status for {job_id}: {e}")
            return None
    
    async def get_review_stats(self) -> Dict[str, Any]:
        """Get overall review statistics."""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Query job counts by status  
            stats_query = """
            SELECT status, COUNT(*) as count
            FROM public.jobs
            GROUP BY status
            """
            
            async with self.db_service.pool.acquire() as conn:
                status_rows = await conn.fetch(stats_query)
            
            status_counts = {row["status"]: row["count"] for row in status_rows}
            
            # Query review performance
            review_stats_query = """
            SELECT 
                COUNT(*) as total_reviews,
                COUNT(*) FILTER (WHERE recommend = true) as recommended_count,
                COUNT(*) FILTER (WHERE recommend = false) as not_recommended_count,
                COUNT(*) FILTER (WHERE error_message IS NOT NULL) as error_count,
                AVG(processing_time_seconds) as avg_processing_time,
                AVG(retry_count) as avg_retry_count
            FROM public.job_reviews
            """
            
            async with self.db_service.pool.acquire() as conn:
                review_row = await conn.fetchrow(review_stats_query)
            
            # Get queue info
            queue_info = self.queue_service.get_queue_info()
            
            return {
                "job_status_counts": status_counts,
                "review_stats": {
                    "total_reviews": review_row["total_reviews"] or 0,
                    "recommended_count": review_row["recommended_count"] or 0,
                    "not_recommended_count": review_row["not_recommended_count"] or 0,
                    "error_count": review_row["error_count"] or 0,
                    "avg_processing_time_seconds": float(review_row["avg_processing_time"]) if review_row["avg_processing_time"] else 0.0,
                    "avg_retry_count": float(review_row["avg_retry_count"]) if review_row["avg_retry_count"] else 0.0,
                },
                "queue_info": queue_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get review stats: {e}")
            return {
                "job_status_counts": {},
                "review_stats": {},
                "queue_info": {}
            }
    
    async def requeue_failed_jobs(self, max_retries: int = 3) -> Dict[str, Any]:
        """
        Re-queue jobs that failed review but haven't exceeded retry limit.
        
        Args:
            max_retries: Maximum retry attempts per job
            
        Returns:
            Summary of re-queuing operation
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Find jobs with status 'pending_review' that have failed reviews under retry limit
            failed_jobs_query = """
            SELECT j.id, j.title, j.company, jr.retry_count, jr.error_message
            FROM public.jobs j
            LEFT JOIN public.job_reviews jr ON j.id = jr.job_id
            WHERE j.status = 'pending_review' 
            AND jr.error_message IS NOT NULL
            AND (jr.retry_count < $1 OR jr.retry_count IS NULL)
            ORDER BY jr.updated_at ASC
            LIMIT 20
            """
            
            async with self.db_service.pool.acquire() as conn:
                failed_jobs = await conn.fetch(failed_jobs_query, max_retries)
            
            if not failed_jobs:
                return {
                    "status": "success",
                    "requeued_count": 0,
                    "message": "No failed jobs to re-queue"
                }
            
            # Re-queue the jobs
            job_ids = [str(job["id"]) for job in failed_jobs]
            results = self.queue_service.enqueue_multiple_job_reviews(job_ids, max_retries)
            
            requeued_count = sum(1 for task_id in results.values() if task_id is not None)
            
            logger.info(f"Re-queued {requeued_count}/{len(failed_jobs)} failed jobs")
            
            return {
                "status": "success",
                "requeued_count": requeued_count,
                "failed_count": len(failed_jobs) - requeued_count,
                "message": f"Re-queued {requeued_count} failed jobs",
                "jobs": [
                    {
                        "job_id": str(job["id"]),
                        "title": job["title"],
                        "company": job["company"],
                        "retry_count": job["retry_count"] or 0,
                        "task_id": results.get(str(job["id"]))
                    }
                    for job in failed_jobs
                ]
            }
            
        except Exception as e:
            error_msg = f"Failed to re-queue failed jobs: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "requeued_count": 0,
                "message": error_msg
            }

    async def queue_single_job(self, job_id: str, max_retries: int = 3) -> Optional[str]:
        """
        Queue a single job for review.

        Args:
            job_id: UUID of the job to queue
            max_retries: Maximum retry attempts

        Returns:
            Task ID if successful, None otherwise
        """
        if not self.initialized:
            await self.initialize()

        try:
            task_id = self.queue_service.enqueue_job_review(job_id, max_retries)

            if task_id:
                logger.info(f"Queued job {job_id} for review with task ID: {task_id}")
                return task_id
            else:
                logger.error(f"Failed to queue job {job_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to queue job {job_id}: {e}")
            return None

    def queue_multiple_job_reviews(self, job_ids: List[str], max_retries: int = 3) -> Dict[str, Optional[str]]:
        """
        Queue multiple jobs for review processing.
        
        Args:
            job_ids: List of job UUIDs to review
            max_retries: Maximum number of retry attempts per job
            
        Returns:
            Dictionary mapping job_id to task_id (or None if failed)
        """
        if not self.initialized:
            # Note: We can't await in a synchronous method called from job_persistence
            # But the service is usually initialized by then.
            pass
            
        try:
            return self.queue_service.enqueue_multiple_job_reviews(job_ids, max_retries)
        except Exception as e:
            logger.error(f"Failed to queue multiple jobs: {e}")
            return {job_id: None for job_id in job_ids}


# Singleton instance
_job_review_service = None

def get_job_review_service() -> JobReviewService:
    """Get the singleton job review service instance."""
    global _job_review_service
    if _job_review_service is None:
        _job_review_service = JobReviewService()
    return _job_review_service