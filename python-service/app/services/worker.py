"""
RQ worker functions for processing job scraping tasks.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from loguru import logger

from .scraping import scrape_jobs_sync
from .database import get_database_service


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