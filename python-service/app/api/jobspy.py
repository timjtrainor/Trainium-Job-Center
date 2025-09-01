"""
JobSpy API endpoints for job scraping functionality.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from ..models.responses import StandardResponse, create_success_response, create_error_response
from ..models.jobspy import JobSearchRequest
from ..services.jobspy_ingestion import get_jobspy_service
from ..services.queue import get_queue_service
from ..services.database import get_database_service
from ..services.scraping import scrape_jobs_async

router = APIRouter()


@router.post("/scrape", response_model=StandardResponse)
async def scrape_jobs(request: JobSearchRequest, mode: Optional[str] = Query(None, description="Execution mode: 'sync' for immediate execution, default is async")):
    """
    Scrape jobs from a specified job board using the provided search criteria.
    
    Args:
        request: JobSearchRequest containing search parameters
        mode: Optional execution mode - 'sync' for immediate execution, default is async queue-based
        
    Returns:
        For async mode (default): StandardResponse containing task_id and run_id for tracking
        For sync mode: StandardResponse containing scraped job data
    """
    try:
        logger.info(f"Job scraping request received: {request.search_term} on {request.site_name}, mode: {mode}")
        
        # Convert request to payload dict
        payload = {
            "site_name": request.site_name.value,
            "search_term": request.search_term,
            "location": request.location,
            "is_remote": request.is_remote,
            "job_type": request.job_type.value if request.job_type else None,
            "results_wanted": request.results_wanted,
            "distance": request.distance,
            "easy_apply": request.easy_apply,
            "hours_old": request.hours_old,
            "google_search_term": request.google_search_term,
            "country_indeed": request.country_indeed,
            "linkedin_fetch_description": request.linkedin_fetch_description,
            "linkedin_company_ids": request.linkedin_company_ids,
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        if mode == "sync":
            # Synchronous execution for small/diagnostic runs
            logger.info(f"Executing sync scrape for {request.site_name}")
            
            # Set shorter timeout for sync mode and limit results
            sync_payload = payload.copy()
            sync_payload["results_wanted"] = min(sync_payload.get("results_wanted", 15), 25)  # Limit to 25 for sync
            
            result = await scrape_jobs_async(sync_payload, min_pause=1, max_pause=3)
            
            return create_success_response(
                data={
                    "jobs": [job.dict() for job in result["jobs"]],
                    "total_found": result["total_found"],
                    "search_metadata": result["search_metadata"],
                    "execution_mode": "sync"
                },
                message=result["message"]
            )
        else:
            # Asynchronous execution (default) - enqueue job
            logger.info(f"Enqueuing async scrape for {request.site_name}")
            
            queue_service = get_queue_service()
            db_service = get_database_service()
            
            # Initialize services if needed
            if not queue_service.initialized:
                await queue_service.initialize()
            if not db_service.initialized:
                await db_service.initialize()
            
            # Generate run ID
            run_id = f"manual_{uuid.uuid4().hex[:8]}"
            
            # Create scrape run record
            scrape_run_id = await db_service.create_scrape_run(
                run_id=run_id,
                site_schedule_id=None,  # Manual run
                task_id="",  # Will be updated after enqueueing
                trigger="manual"
            )
            
            if not scrape_run_id:
                raise HTTPException(status_code=500, detail="Failed to create scrape run record")
            
            # Enqueue the job
            job_info = queue_service.enqueue_scraping_job(
                payload=payload,
                site_schedule_id=None,
                trigger="manual",
                run_id=run_id
            )
            
            if not job_info:
                # Update run status to failed
                await db_service.update_scrape_run_status(
                    run_id=run_id,
                    status="failed",
                    message="Failed to enqueue job"
                )
                raise HTTPException(status_code=500, detail="Failed to enqueue scraping job")
            
            # Update scrape run with task_id
            await db_service.update_scrape_run_status(
                run_id=run_id,
                status="queued",
                message=f"Manual scrape queued for {request.site_name}"
            )
            
            return create_success_response(
                data={
                    "task_id": job_info["task_id"],
                    "run_id": job_info["run_id"],
                    "status": "queued",
                    "execution_mode": "async",
                    "site_name": request.site_name.value,
                    "search_term": request.search_term
                },
                message=f"Job scraping task queued for {request.site_name}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in scrape_jobs endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Job scraping failed: {str(e)}")


@router.get("/scrape/{run_id}", response_model=StandardResponse) 
async def get_scrape_status(run_id: str):
    """
    Get the status of a scraping job by run_id.
    
    Args:
        run_id: The run ID returned from the async scrape request
        
    Returns:
        StandardResponse containing scrape run status and results (if completed)
    """
    try:
        logger.info(f"Getting scrape status for run_id: {run_id}")
        
        db_service = get_database_service()
        queue_service = get_queue_service()
        
        # Initialize services if needed
        if not db_service.initialized:
            await db_service.initialize()
        if not queue_service.initialized:
            await queue_service.initialize()
        
        # Get run details from database
        run_details = await db_service.get_scrape_run_by_id(run_id)
        
        if not run_details:
            raise HTTPException(status_code=404, detail=f"Scrape run {run_id} not found")
        
        response_data = {
            "run_id": run_details["run_id"],
            "status": run_details["status"],
            "trigger": run_details["trigger"],
            "started_at": run_details["started_at"].isoformat() if run_details["started_at"] else None,
            "finished_at": run_details["finished_at"].isoformat() if run_details["finished_at"] else None,
            "requested_pages": run_details["requested_pages"],
            "completed_pages": run_details["completed_pages"],
            "errors_count": run_details["errors_count"],
            "message": run_details["message"],
            "created_at": run_details["created_at"].isoformat()
        }
        
        # If there's a task_id, get queue status too
        if run_details["task_id"]:
            queue_status = queue_service.get_job_status(run_details["task_id"])
            if queue_status:
                response_data["queue_status"] = queue_status["status"]
                if queue_status.get("result"):
                    response_data["result"] = queue_status["result"]
        
        return create_success_response(
            data=response_data,
            message=f"Scrape run {run_id} status: {run_details['status']}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scrape status for {run_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scrape status: {str(e)}")


@router.get("/sites", response_model=StandardResponse)
async def get_supported_sites():
    """
    Get information about supported job sites for scraping.

    Returns:
        StandardResponse containing supported sites data
    """
    try:
        logger.info("Supported sites request received")
        
        jobspy_service = get_jobspy_service()
        result = await jobspy_service.get_supported_sites()
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_supported_sites endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported sites: {str(e)}")


@router.get("/health", response_model=StandardResponse)
async def jobspy_health_check():
    """
    Check the health of the JobSpy ingestion service and queue system.

    Returns:
        StandardResponse containing health status
    """
    try:
        jobspy_service = get_jobspy_service()
        queue_service = get_queue_service()
        db_service = get_database_service()
        
        # Check JobSpy service
        jobspy_health = await jobspy_service.health_check()
        
        # Check queue service
        if not queue_service.initialized:
            await queue_service.initialize()
        queue_info = queue_service.get_queue_info()
        
        # Check database service  
        if not db_service.initialized:
            await db_service.initialize()
        db_health = db_service.initialized
        
        health_data = {
            **jobspy_health,
            "queue_system": {
                "status": "healthy" if queue_service.initialized else "unhealthy",
                "queue_info": queue_info
            },
            "database": {
                "status": "healthy" if db_health else "unhealthy"
            }
        }
        
        from ..models.responses import create_success_response
        return create_success_response(
            data=health_data,
            message="JobSpy service health check completed"
        )
        
    except Exception as e:
        logger.error(f"Error in JobSpy health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/queue/status", response_model=StandardResponse)
async def get_queue_status():
    """
    Get information about the current queue status.
    
    Returns:
        StandardResponse containing queue metrics and status
    """
    try:
        logger.info("Queue status request received")
        
        queue_service = get_queue_service()
        
        if not queue_service.initialized:
            await queue_service.initialize()
        
        queue_info = queue_service.get_queue_info()
        
        return create_success_response(
            data=queue_info,
            message="Queue status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")