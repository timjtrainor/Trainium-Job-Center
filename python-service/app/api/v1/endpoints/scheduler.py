"""
Scheduler API endpoints for managing job scraping schedules.
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.responses import StandardResponse, create_success_response
from app.services.scheduler import get_scheduler_service

router = APIRouter()


@router.post("/run", response_model=StandardResponse)
async def run_scheduler():
    """
    Manually trigger the scheduler to process due site schedules.
    
    Returns:
        StandardResponse containing number of jobs enqueued
    """
    try:
        logger.info("Manual scheduler run requested")
        
        scheduler_service = get_scheduler_service()
        
        if not scheduler_service.initialized:
            await scheduler_service.initialize()
        
        jobs_enqueued = await scheduler_service.process_scheduled_sites()
        
        return create_success_response(
            data={"jobs_enqueued": jobs_enqueued},
            message=f"Scheduler processed {jobs_enqueued} site schedules"
        )
        
    except Exception as e:
        logger.error(f"Error in manual scheduler run: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scheduler run failed: {str(e)}")


@router.get("/status", response_model=StandardResponse)
async def get_scheduler_status():
    """
    Get the current status of the scheduler.
    
    Returns:
        StandardResponse containing scheduler status information
    """
    try:
        logger.info("Scheduler status request received")
        
        scheduler_service = get_scheduler_service()
        
        if not scheduler_service.initialized:
            await scheduler_service.initialize()
        
        status = await scheduler_service.get_scheduler_status()
        
        return create_success_response(
            data=status,
            message="Scheduler status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")