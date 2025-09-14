"""
RQ worker functions for processing job scraping tasks.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from loguru import logger

from ..jobspy.scraping import scrape_jobs_sync
from .database import get_database_service
from .job_persistence import persist_jobs


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
        if result.get("jobs") and result.get("status") in ["succeeded", "partial"]:
            try:
                site_name = payload.get("site_name", "unknown")
                persistence_summary = loop.run_until_complete(
                    persist_jobs(records=result["jobs"], site_name=site_name)
                )
                logger.info(f"Run {run_id}: Persisted jobs - {persistence_summary}")
                
                # Add persistence info to result for logging
                result["persistence_summary"] = persistence_summary
                
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
        
        # Prepare job data for CrewAI
        crew_input = {
            "title": job_data.get("title", ""),
            "company": job_data.get("company", ""),
            "location": job_data.get("location_city") or job_data.get("location_state") or "Remote",
            "description": job_data.get("description", ""),
            "url": job_data.get("job_url", ""),
            "is_remote": job_data.get("is_remote", False),
            "job_type": job_data.get("job_type", ""),
            "salary_info": {
                "min_amount": job_data.get("min_amount"),
                "max_amount": job_data.get("max_amount"),
                "currency": job_data.get("currency"),
                "interval": job_data.get("interval")
            }
        }
        
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
        final_result = crew_result.get("final", {}) if isinstance(crew_result, dict) else {}
        
        review_data = {
            "recommend": final_result.get("recommend", False),
            "confidence": final_result.get("confidence", "low"),
            "rationale": final_result.get("rationale", "No rationale provided"),
            "personas": crew_result.get("personas", []),
            "tradeoffs": crew_result.get("tradeoffs", []),
            "actions": crew_result.get("actions", []),
            "sources": crew_result.get("sources", []),
            "crew_output": crew_result,
            "processing_time_seconds": processing_time,
            "crew_version": "job_posting_review_v1",
            "model_used": "CrewAI",
            "retry_count": retry_count
        }
        
        # Store review results  
        success = loop.run_until_complete(db_service.insert_job_review(job_id, review_data))
        if not success:
            raise RuntimeError("Failed to store review results")
        
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