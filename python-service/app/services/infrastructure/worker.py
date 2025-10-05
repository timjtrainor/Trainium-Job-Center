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
    
    try:
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


def process_job_review(job_id: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Worker function for processing job review tasks using CrewAI.
    
    Args:
        job_id: UUID of the job to review
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary with review results and status
    """
    import time
    import asyncio
    from ..crewai.job_posting_review.crew import run_crew
    
    logger.info(f"Processing job review for job_id: {job_id}")
    start_time = time.time()
    
    # Initialize database service
    db_service = get_database_service()
    
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
        
        # Update job status to 'in_review'
        success = loop.run_until_complete(
            db_service.update_job_status(job_id, "in_review")
        )
        if not success:
            raise RuntimeError(f"Failed to update job status to 'in_review'")
        
        # Fetch job details
        job_data = loop.run_until_complete(db_service.get_job_by_id(job_id))
        if not job_data:
            raise RuntimeError(f"Job not found: {job_id}")
        
        logger.info(f"Job review started - ID: {job_id}, Title: '{job_data.get('title')}', Company: {job_data.get('company')}")
        
        # Check if review already exists (for retry scenarios)
        existing_review = loop.run_until_complete(db_service.get_job_review(job_id))
        retry_count = existing_review.get("retry_count", 0) if existing_review else 0
        
        if retry_count >= max_retries:
            error_msg = f"Maximum retry attempts ({max_retries}) reached for job {job_id}"
            logger.error(error_msg)
            
            # Update job status to error and store error in job_reviews
            loop.run_until_complete(db_service.update_job_status(job_id, "error"))
            loop.run_until_complete(db_service.insert_job_review(job_id, {
                "recommend": False,
                "confidence": "low",
                "rationale": error_msg,
                "error_message": error_msg,
                "retry_count": retry_count,
                "processing_time_seconds": time.time() - start_time
            }))
            
            return {
                "status": "failed",
                "job_id": job_id,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "message": error_msg,
                "retry_count": retry_count
            }
        
        # Prepare structured job data for CrewAI (skip job_intake_agent - already structured)
        crew_input = {
            "title": job_data.get("title", ""),
            "company": job_data.get("company", ""),
            "location": job_data.get("location_city") or job_data.get("location_state") or "Remote",
            "description": job_data.get("description", ""),
            "job_type": job_data.get("job_type", ""),
            "seniority": "Senior",  # Default as this field may not exist in jobs table
            "salary": {
                "min_amount": job_data.get("min_amount"),
                "max_amount": job_data.get("max_amount"),
                "currency": job_data.get("currency", "USD"),
                "interval": job_data.get("interval", "yearly")
            }
        }

        crew_input = _coerce_decimals(crew_input)
        
        # Run CrewAI job posting review
        logger.info(f"Running CrewAI review for job {job_id}")
        crew_result = run_crew(crew_input, correlation_id=job_id)
        
        processing_time = time.time() - start_time
        
        # Handle crew errors
        if "error" in crew_result:
            error_msg = f"CrewAI error: {crew_result['error']}"
            logger.error(f"CrewAI failed for job {job_id}: {error_msg}")
            
            # Store error and increment retry count
            review_data = {
                "recommend": False,
                "confidence": "low", 
                "rationale": error_msg,
                "error_message": error_msg,
                "retry_count": retry_count + 1,
                "processing_time_seconds": processing_time,
                "crew_output": crew_result
            }
            
            loop.run_until_complete(db_service.insert_job_review(job_id, review_data))
            
            # If under retry limit, keep status as pending_review for retry
            if retry_count + 1 < max_retries:
                loop.run_until_complete(db_service.update_job_status(job_id, "pending_review"))
                return {
                    "status": "retry",
                    "job_id": job_id,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "message": f"Review failed, will retry. Attempt {retry_count + 1}/{max_retries}",
                    "retry_count": retry_count + 1
                }
            else:
                # Max retries reached
                loop.run_until_complete(db_service.update_job_status(job_id, "error"))
                return {
                    "status": "failed",
                    "job_id": job_id,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "message": f"Review failed after {max_retries} attempts",
                    "retry_count": retry_count + 1
                }
        
        # Parse successful crew result
        if isinstance(crew_result, dict):
            final_result = crew_result.get("final", {})
            prefilter = crew_result.get("pre_filter", {})
        else:
            final_result = {}
            prefilter = {}

        if not isinstance(final_result, dict):
            final_result = {}
        if not isinstance(prefilter, dict):
            prefilter = {}

        rationale = (
            final_result.get("rationale")
            or prefilter.get("reason")
            or "No rationale provided"
        )

        review_data = {
            "recommend": final_result.get(
                "recommend", prefilter.get("recommend", False)
            ),
            "confidence": final_result.get("confidence", "low"),
            "rationale": rationale,
            "personas": crew_result.get("personas", []),
            "tradeoffs": crew_result.get("tradeoffs", []),
            "actions": crew_result.get("actions", []),
            "sources": crew_result.get("sources", []),
            "overall_alignment_score": crew_result.get("overall_alignment_score"),  # Extract for database column
            "tldr_summary": crew_result.get("tldr_summary"),  # Include for crew_output JSON (no separate column)
            "crew_output": crew_result,
            "processing_time_seconds": processing_time,
            "crew_version": "job_posting_review_v1",
            "model_used": "CrewAI",
            "retry_count": retry_count
        }
        
        logger.info(f"Prepared review data for job_id {job_id}: recommend={review_data['recommend']}, confidence={review_data['confidence']}")
        
        # Store review results  
        logger.info(f"Storing review results for job_id: {job_id}")
        success = loop.run_until_complete(db_service.insert_job_review(job_id, review_data))
        if not success:
            error_msg = f"Failed to store review results in database for job_id: {job_id}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Update job status to 'reviewed'
        success = loop.run_until_complete(db_service.update_job_status(job_id, "reviewed"))
        if not success:
            logger.warning(f"Failed to update job status to 'reviewed' for {job_id}")
        
        result = {
            "status": "completed",
            "job_id": job_id,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Job review completed for '{job_data.get('title')}' at '{job_data.get('company')}'",
            "recommend": review_data["recommend"],
            "confidence": review_data["confidence"],
            "processing_time_seconds": processing_time,
            "retry_count": retry_count
        }
        
        logger.info(f"Job review completed successfully for job_id: {job_id} (recommend: {review_data['recommend']}, confidence: {review_data['confidence']})")
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Job review error for job_id {job_id}: {str(e)}"
        logger.error(error_msg)
        
        try:
            # Get current retry count
            existing_review = loop.run_until_complete(db_service.get_job_review(job_id)) if loop else None
            retry_count = existing_review.get("retry_count", 0) if existing_review else 0
            
            # Store error information
            error_review_data = {
                "recommend": False,
                "confidence": "low",
                "rationale": f"Processing failed: {str(e)}",
                "error_message": error_msg,
                "retry_count": retry_count + 1,
                "processing_time_seconds": processing_time
            }
            
            if loop:
                loop.run_until_complete(db_service.insert_job_review(job_id, error_review_data))
                
                # Set status based on retry count
                if retry_count + 1 < max_retries:
                    loop.run_until_complete(db_service.update_job_status(job_id, "pending_review"))
                else:
                    loop.run_until_complete(db_service.update_job_status(job_id, "error"))
        except Exception as store_error:
            logger.error(f"Failed to store error information: {store_error}")
        
        return {
            "status": "failed", 
            "job_id": job_id,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "message": error_msg,
            "error": str(e),
            "processing_time_seconds": processing_time
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
    from ..crewai.linkedin_job_search.crew import run_linkedin_job_search as execute_linkedin_search
    
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
