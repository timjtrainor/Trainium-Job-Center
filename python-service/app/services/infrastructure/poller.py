"""
Poller service for checking jobs table and enqueuing pending review jobs.
"""
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime, timezone

from ...core.config import get_settings
from .database import get_database_service
from .queue import get_queue_service


class PollerService:
    """Service for polling jobs table and enqueuing pending review jobs to Redis."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_service = get_database_service()
        self.queue_service = get_queue_service()
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize poller dependencies."""
        try:
            db_init = await self.db_service.initialize()
            queue_init = await self.queue_service.initialize()
            
            self.initialized = db_init and queue_init
            
            if self.initialized:
                logger.info("Poller service initialized successfully")
            else:
                logger.error("Failed to initialize poller dependencies")
                
            return self.initialized
        except Exception as e:
            logger.error(f"Failed to initialize poller: {str(e)}")
            return False

    async def get_pending_review_jobs(self) -> List[Dict[str, Any]]:
        """Get jobs with status='pending_review' from the database, ensuring deduplication by canonical_key."""
        if not self.initialized:
            await self.initialize()

        query = """
        SELECT id, title, company, site, job_url, ingested_at, canonical_key
        FROM public.jobs
        WHERE status = 'pending_review'
        ORDER BY ingested_at ASC
        LIMIT 100
        """
        
        try:
            async with self.db_service.pool.acquire() as conn:
                rows = await conn.fetch(query)
                jobs = [dict(row) for row in rows]
                logger.debug(f"Found {len(jobs)} jobs pending review")
                return jobs
        except Exception as e:
            logger.error(f"Failed to fetch pending review jobs: {str(e)}")
            return []

    async def update_job_status(self, job_id: str, new_status: str) -> bool:
        """Update job status in the database."""
        if not self.initialized:
            await self.initialize()
        
        query = """
        UPDATE public.jobs 
        SET status = $2, updated_at = CURRENT_TIMESTAMP 
        WHERE id = $1
        """
        
        try:
            async with self.db_service.pool.acquire() as conn:
                result = await conn.execute(query, job_id, new_status)
                success = result == "UPDATE 1"
                if success:
                    logger.debug(f"Updated job {job_id} status to {new_status}")
                else:
                    logger.warning(f"Failed to update job {job_id} - may not exist")
                return success
        except Exception as e:
            logger.error(f"Failed to update job {job_id} status: {str(e)}")
            return False

    def enqueue_job_review(self, job_id: str, job_data: Dict[str, Any]) -> Optional[str]:
        """Enqueue a job for review processing."""
        if not self.initialized:
            logger.error("Poller service not initialized")
            return None

        try:
            logger.debug(
                "Submitting job for review",
                job_id=job_id,
                title=job_data.get("title"),
                company=job_data.get("company"),
                site=job_data.get("site"),
            )

            # Use the queue service's job review method with the job ID
            task_id = self.queue_service.enqueue_job_review(job_id)

            if task_id:
                logger.info(f"Enqueued job {job_id} for review - task_id: {task_id}")

            return task_id
            
        except Exception as e:
            logger.error(f"Failed to enqueue job {job_id} for review: {str(e)}")
            return None

    async def poll_and_enqueue_jobs(self) -> int:
        """
        Main polling function: get pending jobs, enqueue them, and update status.

        Returns:
            Number of jobs successfully enqueued
        """
        if not self.initialized:
            logger.warning("Poller not initialized")
            return 0

        # Check feature flags
        if self.settings.disable_job_posting_review or not self.settings.job_review_enabled:
            logger.info("Job posting review is disabled - skipping polling cycle")
            return 0

        try:
            logger.debug("Starting poll cycle for pending review jobs")
            
            # Get jobs pending review
            pending_jobs = await self.get_pending_review_jobs()
            
            if not pending_jobs:
                logger.debug("No jobs pending review found")
                return 0
            
            enqueued_count = 0
            processed_canonical_keys = set()

            for job in pending_jobs:
                job_id = str(job["id"])
                canonical_key = job.get("canonical_key")

                # Skip if we've already processed a job with this canonical_key
                if canonical_key and canonical_key in processed_canonical_keys:
                    logger.debug(f"Skipping duplicate job {job_id} - canonical_key {canonical_key} already processed")
                    # Update status to skipped_duplicate to avoid reprocessing
                    await self.update_job_status(job_id, "duplicate")
                    continue

                # Mark this canonical_key as processed
                if canonical_key:
                    processed_canonical_keys.add(canonical_key)

                try:
                    # Enqueue job for review
                    task_id = self.enqueue_job_review(job_id, job)
                    
                    if task_id:
                        # Update status to in_review
                        success = await self.update_job_status(job_id, "in_review")
                        
                        if success:
                            enqueued_count += 1
                            logger.info(
                                f"Job enqueued successfully - "
                                f"job_id: {job_id}, "
                                f"title: '{job.get('title', 'N/A')}', "
                                f"company: {job.get('company', 'N/A')}, "
                                f"site: {job.get('site', 'N/A')}, "
                                f"task_id: {task_id}"
                            )
                        else:
                            logger.error(f"Failed to update status for job {job_id}")
                    else:
                        logger.error(f"Failed to enqueue job {job_id}")
                        
                except Exception as e:
                    logger.error(f"Error processing job {job_id}: {str(e)}")
                    continue
            
            if enqueued_count > 0:
                logger.info(f"Poll cycle complete: {enqueued_count} jobs enqueued for review")
            else:
                logger.debug("Poll cycle complete: no jobs enqueued")
                
            return enqueued_count
            
        except Exception as e:
            logger.error(f"Error in poll cycle: {str(e)}")
            return 0

    async def start_polling_loop(self):
        """Start the continuous polling loop."""
        logger.info(f"Starting poller service - poll interval: {self.settings.poll_interval_minutes} minutes")
        
        # Initialize if not already done
        if not self.initialized:
            await self.initialize()
            
        if not self.initialized:
            logger.error("Failed to initialize poller service")
            return
            
        poll_interval_seconds = self.settings.poll_interval_minutes * 60
        
        try:
            import gc
            psutil = None
            try:
                import psutil
            except ImportError:
                logger.warning("psutil not found, memory logging disabled")
                
            import os
            
            process = psutil.Process(os.getpid()) if psutil else None
            
            while True:
                try:
                    # Log memory usage before cycle
                    if process:
                        mem_info = process.memory_info()
                        logger.info(f"Poller memory usage: {mem_info.rss / 1024 / 1024:.2f} MB")
                    
                    enqueued_count = await self.poll_and_enqueue_jobs()
                    logger.debug(f"Poll cycle complete, sleeping for {self.settings.poll_interval_minutes} minutes")
                    
                    # Explicit garbage collection
                    gc.collect()
                    
                except Exception as e:
                    logger.error(f"Error in polling cycle: {str(e)}")
                    
                # Wait for next poll cycle
                await asyncio.sleep(poll_interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("Poller service stopped by user")
        except Exception as e:
            logger.error(f"Poller service error: {str(e)}")
            raise


# Global service instance
_poller_service: Optional[PollerService] = None


def get_poller_service() -> PollerService:
    """Get or create the global poller service instance."""
    global _poller_service
    if _poller_service is None:
        _poller_service = PollerService()
    return _poller_service
