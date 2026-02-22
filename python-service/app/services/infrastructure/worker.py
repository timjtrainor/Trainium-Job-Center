"""
RQ worker functions for processing job scraping tasks.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
from loguru import logger

from ..jobspy.scraping import scrape_jobs_sync, normalize_job_to_scraped_job
from .database import get_database_service
from .job_persistence import persist_jobs
from ..jobspy.glassdoor_scraper import scrape_glassdoor_job_description, PLAYWRIGHT_AVAILABLE


def _coerce_decimals(value: Any) -> Any:
    """Recursively convert Decimal values to floats for JSON compatibility."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _coerce_decimals(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_coerce_decimals(item) for item in value]
    return value


def scrape_jobs_worker(site_schedule_id: Optional[str] = None, 
                      payload: Optional[Dict[str, Any]] = None,
                      run_id: Optional[str] = None,
                      min_pause: int = 2, 
                      max_pause: int = 8,
                      max_retries: int = 3) -> Dict[str, Any]:
    """
    Worker function that processes job scraping tasks.
    
    Args:
        site_schedule_id: ID of site schedule (for scheduled runs)
        payload: Job search parameters
        run_id: Unique run identifier for tracking
        min_pause: Minimum pause between requests
        max_pause: Maximum pause between requests  
        max_retries: Maximum retry attempts
        
    Returns:
        Dictionary with scraping results and metadata
    """
    
    # Generate run_id if not provided
    if not run_id:
        run_id = f"run_{uuid.uuid4().hex[:8]}"
    
    # Initialize database service
    db_service = get_database_service()
    
    logger.info(f"Worker started for run_id: {run_id}, site_schedule_id: {site_schedule_id}")
    
    site_name = payload.get("site_name", "unknown") if payload else "unknown"
    site_name_clean = site_name.strip().lower()
    lock_key = f"site_active_job:{site_name_clean}"
    lock_value = None
    
    try:
        # Check if we own a lock for this run
        from .queue import get_queue_service
        queue_service = get_queue_service()
        # Ensure queue service is initialized
        if not queue_service.initialized:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                loop.run_until_complete(queue_service.initialize())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(queue_service.initialize())
        
        existing_lock = queue_service.check_redis_lock(lock_key)
        if existing_lock:
            val = existing_lock.decode('utf-8') if isinstance(existing_lock, bytes) else str(existing_lock)
            if val.startswith(f"{run_id}:"):
                lock_value = val
                logger.info(f"Run {run_id}: Identified own site lock for {site_name_clean}")
        # Update run status to 'running'
        loop = None
        try:
            import asyncio
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Ensure database is initialized
        if not db_service.initialized:
            loop.run_until_complete(db_service.initialize())
        
        # Update status to running
        started_at = datetime.now(timezone.utc)
        loop.run_until_complete(
            db_service.update_scrape_run_status(
                run_id=run_id,
                status="running", 
                started_at=started_at
            )
        )
        
        logger.info(f"Run {run_id}: Status updated to 'running'")
        
        # Execute the scraping
        result = scrape_jobs_sync(payload, min_pause, max_pause)
        
        # Persist scraped jobs if scraping was successful
        persistence_summary = None
        enrichment_summary = None
        if result.get("jobs") and result.get("status") in ["succeeded", "partial"]:
            try:
                site_name = payload.get("site_name", "unknown")
                persistence_summary = loop.run_until_complete(
                    persist_jobs(records=result["jobs"], site_name=site_name)
                )
                logger.info(f"Run {run_id}: Persisted jobs - {persistence_summary}")

                # Add persistence info to result for logging
                result["persistence_summary"] = persistence_summary

                # Auto-enrich Glassdoor jobs with full descriptions
                if site_name.lower() == "glassdoor" and PLAYWRIGHT_AVAILABLE and persistence_summary.get("inserted", 0) > 0:
                    logger.info(f"Run {run_id}: Starting Glassdoor enrichment for {persistence_summary['inserted']} new jobs")
                    enrichment_summary = loop.run_until_complete(
                        _enrich_glassdoor_jobs(result.get("jobs", []), db_service)
                    )
                    logger.info(f"Run {run_id}: Glassdoor enrichment - {enrichment_summary}")
                    result["glassdoor_enrichment_summary"] = enrichment_summary

            except Exception as e:
                logger.error(f"Run {run_id}: Failed to persist jobs: {e}")
                # Don't fail the entire job for persistence errors
                result["persistence_summary"] = {
                    "inserted": 0,
                    "skipped_duplicates": 0,
                    "errors": [f"Persistence failed: {str(e)}"]
                }
        
        # Update final status
        finished_at = datetime.now(timezone.utc)
        final_status = result.get("status", "failed")
        
        loop.run_until_complete(
            db_service.update_scrape_run_status(
                run_id=run_id,
                status=final_status,
                finished_at=finished_at,
                requested_pages=result.get("requested_pages", 0),
                completed_pages=result.get("completed_pages", 0), 
                errors_count=result.get("errors_count", 0),
                message=result.get("message", "")
            )
        )
        
        logger.info(f"Run {run_id}: Completed with status '{final_status}', found {result.get('total_found', 0)} jobs")
        
        # Add worker metadata to result
        result["run_id"] = run_id
        result["site_schedule_id"] = site_schedule_id
        result["worker_completed_at"] = finished_at.isoformat()
        
        return result
        
    except Exception as e:
        error_msg = f"Worker error for run_id {run_id}: {str(e)}"
        logger.error(error_msg)
        
        # Update status to failed
        try:
            finished_at = datetime.now(timezone.utc) 
            loop.run_until_complete(
                db_service.update_scrape_run_status(
                    run_id=run_id,
                    status="failed",
                    finished_at=finished_at,
                    errors_count=1,
                    message=error_msg[:500]  # Truncate long error messages
                )
            )
        except:
            logger.error(f"Failed to update run status for failed job {run_id}")
        
        return {
            "status": "failed",
            "run_id": run_id,
            "site_schedule_id": site_schedule_id,
            "message": error_msg,
            "total_found": 0,
            "requested_pages": 0,
            "completed_pages": 0,
            "errors_count": 1
        }
    finally:
        # Always release the site lock if we own it
        if lock_value:
            try:
                from .queue import get_queue_service
                queue_service = get_queue_service()
                if queue_service.initialize():
                    if queue_service.release_redis_lock(lock_key, lock_value):
                        logger.info(f"Run {run_id}: Released site lock for {site_name_clean}")
                    else:
                        logger.warning(f"Run {run_id}: Failed to release site lock for {site_name_clean} (may have expired or been cleared)")
            except Exception as le:
                logger.error(f"Run {run_id}: Error while releasing lock: {le}")


def process_job_review(job_id: str, max_retries: int = 3, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Worker function for processing job review tasks using LangGraph.
    
    Args:
        job_id: UUID of the job to review
        max_retries: Maximum number of retry attempts
        user_id: Optional user ID for context
        
    Returns:
        Dictionary with review results and status
    """
    import asyncio
    import os
    import json
    import redis
    
    logger.info(f"Processing job review for job_id: {job_id}")
    start_time = datetime.now(timezone.utc)
    
    # Initialize database service
    db_service = get_database_service()
    
    # Check for Webhook Bridge Redirection
    webhook_enabled = os.getenv("WEBHOOK_BRIDGE_ENABLED", "true").lower() == "true"
    
    try:
        # Set up async event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if webhook_enabled:
            logger.info(f"Webhook redirection is enabled. Redirecting job {job_id} to Redis.")
            
            # 1. Fetch job data
            job_data = loop.run_until_complete(db_service.get_job_by_id(job_id))
            if not job_data:
                logger.error(f"Job {job_id} not found in DB for redirection.")
                return {"status": "error", "message": "Job not found"}

            # 2. Check for duplicate status
            duplicate_status = job_data.get("duplicate_status")
            # Relax check to allow None (which might happen if the column is null for older records or specific ingestion flows)
            if duplicate_status not in ["original", None]:
                logger.info(f"Skipping webhook redirection for job {job_id}: status is '{duplicate_status}' (not 'original' or None)")
                return {
                    "status": "skipped_duplicate",
                    "job_id": job_id,
                    "duplicate_status": duplicate_status
                }

            # 3. Publish to Redis channel
            from .queue import get_queue_service
            queue_service = get_queue_service()
            
            # Ensure queue service is initialized
            if not queue_service.initialized:
                loop.run_until_complete(queue_service.initialize())
            
            redis_conn = queue_service.redis_conn
            if not redis_conn:
                logger.error(f"Redis connection not available for job {job_id}")
                return {"status": "error", "message": "Redis connection error"}
            
            channel = os.getenv("REDIS_CHANNEL", "job_review_webhook")
            payload = {
                "job_id": str(job_id),
                "title": job_data.get("title"),
                "company": job_data.get("company"),
                "description": job_data.get("description"),
                "user_id": user_id or "system"
            }
            
            redis_conn.publish(channel, json.dumps(payload))
            logger.success(f"Successfully published job {job_id} to Redis channel {channel}")
            
            # 4. Update job status to 'testing'
            loop.run_until_complete(db_service.update_job_status(job_id, "testing"))
            
            return {
                "status": "redirected_to_webhook",
                "job_id": job_id,
                "channel": channel,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            
        # Standard Mode (Deprecated/Placeholder)
        logger.warning(f"Standard job review mode is deprecated. Job {job_id} was not redirected.")
        return {
            "status": "ignored",
            "job_id": job_id,
            "message": "Direct LangGraph workflow is removed. Use Webhook/ActivePieces."
        }
            
    except Exception as e:
        logger.error(f"Error in process_job_review for {job_id}: {e}")
        return {
            "status": "error",
            "job_id": job_id,
            "error": str(e),
            "processed_at": datetime.now(timezone.utc).isoformat()
        }


def run_linkedin_job_search(
    site_schedule_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Worker function for processing LinkedIn job search tasks using CrewAI.
    
    Args:
        site_schedule_id: ID of site schedule (for scheduled runs)
        payload: LinkedIn job search parameters
        run_id: Unique run identifier for tracking
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary with search results and metadata
    """
    import time
    import asyncio
    # CrewAI is deprecated, using local search instead
    # from ..crewai.linkedin_job_search.crew import run_linkedin_job_search as execute_linkedin_search
    logger.warning(f"Run {run_id}: CrewAI is disabled. Skipping LinkedIn job search via Crew.")
    return {
        "run_id": run_id,
        "status": "skipped",
        "message": "CrewAI is deprecated and disabled."
    }
    
    # Generate run_id if not provided
    if not run_id:
        run_id = f"linkedin_run_{uuid.uuid4().hex[:8]}"
    
    # Initialize database service
    db_service = get_database_service()
    
    logger.info(f"LinkedIn job search worker started for run_id: {run_id}, site_schedule_id: {site_schedule_id}")
    start_time = time.time()
    
    try:
        # Set up async event loop
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Initialize database connection
        if not db_service.initialized:
            loop.run_until_complete(db_service.initialize())
        
        # Update run status to 'running'
        started_at = datetime.now(timezone.utc)
        loop.run_until_complete(
            db_service.update_scrape_run_status(
                run_id=run_id,
                status="running", 
                started_at=started_at
            )
        )
        
        logger.info(f"LinkedIn run {run_id}: Status updated to 'running'")
        
        # Parse search parameters from payload
        if not payload:
            payload = {}
        
        # Extract LinkedIn search parameters with defaults
        keywords = payload.get("keywords", payload.get("search_term", "software engineer"))
        location = payload.get("location", "remote")
        job_type = payload.get("job_type")
        date_posted = payload.get("date_posted")
        experience_level = payload.get("experience_level")
        remote = payload.get("is_remote", payload.get("remote", True))
        limit = payload.get("results_wanted", payload.get("limit", 25))
        
        logger.info(f"LinkedIn run {run_id}: Executing search - keywords: '{keywords}', location: '{location}', limit: {limit}")
        
        # Execute the LinkedIn job search using CrewAI
        search_result = execute_linkedin_search(
            keywords=keywords,
            location=location,
            job_type=job_type,
            date_posted=date_posted,
            experience_level=experience_level,
            remote=remote,
            limit=limit
        )
        
        processing_time = time.time() - start_time
        
        # Handle search errors
        if not search_result.get("success", True) or "error" in search_result:
            error_msg = f"LinkedIn search failed: {search_result.get('error', 'Unknown error')}"
            logger.error(f"LinkedIn run {run_id}: {error_msg}")
            
            # Update status to failed
            finished_at = datetime.now(timezone.utc)
            loop.run_until_complete(
                db_service.update_scrape_run_status(
                    run_id=run_id,
                    status="failed",
                    finished_at=finished_at,
                    errors_count=1,
                    message=error_msg[:500]
                )
            )
            
            return {
                "status": "failed",
                "run_id": run_id,
                "site_schedule_id": site_schedule_id,
                "message": error_msg,
                "total_found": 0,
                "processing_time_seconds": processing_time,
                "worker_completed_at": finished_at.isoformat()
            }
        
        # Persist LinkedIn jobs if search was successful
        jobs_found = search_result.get("consolidated_jobs", [])
        total_jobs = search_result.get("total_jobs", len(jobs_found))

        persistence_summary = None
        if jobs_found:
            try:
                # Normalize LinkedIn search results to standardized ScrapedJob format
                normalized_jobs = []
                for job in jobs_found:
                    normalized_job = normalize_job_to_scraped_job(job, "linkedin")
                    normalized_jobs.append(normalized_job)

                persistence_summary = loop.run_until_complete(
                    persist_jobs(records=normalized_jobs, site_name="linkedin")
                )
                logger.info(f"LinkedIn run {run_id}: Normalized and persisted {len(normalized_jobs)} jobs - {persistence_summary}")

            except Exception as e:
                logger.error(f"LinkedIn run {run_id}: Failed to normalize/persist jobs: {e}")
                persistence_summary = {
                    "inserted": 0,
                    "skipped_duplicates": 0,
                    "errors": [f"Normalization/persistence failed: {str(e)}"]
                }
        
        # Update final status
        finished_at = datetime.now(timezone.utc)
        final_status = "succeeded" if jobs_found else "partial"
        
        loop.run_until_complete(
            db_service.update_scrape_run_status(
                run_id=run_id,
                status=final_status,
                finished_at=finished_at,
                requested_pages=1,  # LinkedIn searches are single requests
                completed_pages=1 if search_result.get("success", True) else 0,
                errors_count=0,
                message=f"LinkedIn search completed: {total_jobs} jobs found"
            )
        )
        
        logger.info(f"LinkedIn run {run_id}: Completed with status '{final_status}', found {total_jobs} jobs")
        
        # Add worker metadata to result
        result = {
            "status": final_status,
            "run_id": run_id,
            "site_schedule_id": site_schedule_id,
            "total_found": total_jobs,
            "jobs": jobs_found,
            "persistence_summary": persistence_summary,
            "processing_time_seconds": processing_time,
            "worker_completed_at": finished_at.isoformat(),
            "linkedin_search_metadata": search_result.get("consolidation_metadata", {}),
            "requested_pages": 1,
            "completed_pages": 1 if search_result.get("success", True) else 0,
            "errors_count": 0,
            "message": f"LinkedIn search completed: {total_jobs} jobs found"
        }
        
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"LinkedIn job search worker error for run_id {run_id}: {str(e)}"
        logger.error(error_msg)
        
        # Update status to failed
        try:
            finished_at = datetime.now(timezone.utc)
            loop.run_until_complete(
                db_service.update_scrape_run_status(
                    run_id=run_id,
                    status="failed",
                    finished_at=finished_at,
                    errors_count=1,
                    message=error_msg[:500]
                )
            )
        except Exception as db_error:
            logger.error(f"Failed to update run status for failed LinkedIn job {run_id}: {db_error}")
        
        return {
            "status": "failed",
            "run_id": run_id,
            "site_schedule_id": site_schedule_id,
            "message": error_msg,
            "total_found": 0,
            "processing_time_seconds": processing_time,
            "requested_pages": 1,
            "completed_pages": 0,
            "errors_count": 1
        }


async def _enrich_glassdoor_jobs(jobs: list, db_service) -> Dict[str, Any]:
    """
    Enrich Glassdoor jobs with full descriptions using Playwright scraping.

    Args:
        jobs: List of scraped job dictionaries with job_url fields
        db_service: Database service instance

    Returns:
        Summary dict: {enriched: int, failed: int, skipped: int}
    """
    import asyncio

    enriched = 0
    failed = 0
    skipped = 0

    for job in jobs:
        try:
            # Get job URL from ScrapedJob object or dict
            if hasattr(job, 'job_url'):
                job_url = job.job_url
            else:
                job_url = job.get('job_url')

            if not job_url:
                logger.warning(f"Skipping enrichment - no job_url for job: {job}")
                skipped += 1
                continue

            # Check if job already has a description
            if hasattr(job, 'description'):
                existing_desc = job.description
            else:
                existing_desc = job.get('description')

            if existing_desc and len(existing_desc) > 100:
                logger.debug(f"Skipping enrichment - job already has description: {job_url}")
                skipped += 1
                continue

            # Scrape full description
            logger.info(f"Enriching Glassdoor job: {job_url}")
            description = await scrape_glassdoor_job_description(job_url, timeout=30000)

            if description:
                # Find the job ID in database by job_url to update it
                async with db_service.pool.acquire() as conn:
                    job_id = await conn.fetchval(
                        "SELECT id FROM jobs WHERE LOWER(site) = 'glassdoor' AND job_url = $1 LIMIT 1",
                        job_url
                    )

                    if job_id:
                        await conn.execute(
                            "UPDATE jobs SET description = $1 WHERE id = $2",
                            description,
                            job_id
                        )
                        enriched += 1
                        logger.info(f"✓ Enriched Glassdoor job {job_id}: {len(description)} chars")
                    else:
                        logger.warning(f"Could not find job in DB for URL: {job_url}")
                        skipped += 1
            else:
                failed += 1
                logger.warning(f"✗ Failed to scrape description for: {job_url}")

            # Rate limiting: 2 second pause between requests
            await asyncio.sleep(2)

        except Exception as e:
            failed += 1
            logger.error(f"Error enriching Glassdoor job: {e}")
            continue

    return {
        "enriched": enriched,
        "failed": failed,
        "skipped": skipped
    }
