"""
JobSpy API endpoints for job scraping functionality.
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..models.responses import StandardResponse
from ..models.jobspy import JobSearchRequest
from ..services.jobspy_ingestion import get_jobspy_service

router = APIRouter()


@router.post("/scrape", response_model=StandardResponse)
async def scrape_jobs(request: JobSearchRequest):
    """
    Scrape jobs from a specified job board using the provided search criteria.
    
    Args:
        request: JobSearchRequest containing search parameters
        
    Returns:
        StandardResponse containing scraped job data
    """
    try:
        logger.info(f"Job scraping request received: {request.search_term} on {request.site_name}")
        
        jobspy_service = get_jobspy_service()
        result = await jobspy_service.scrape_jobs_async(request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in scrape_jobs endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Job scraping failed: {str(e)}")


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
    Check the health of the JobSpy ingestion service.
    
    Returns:
        StandardResponse containing health status
    """
    try:
        jobspy_service = get_jobspy_service()
        health_data = await jobspy_service.health_check()
        
        from ..models.responses import create_success_response
        return create_success_response(
            data=health_data,
            message="JobSpy service health check completed"
        )
        
    except Exception as e:
        logger.error(f"Error in JobSpy health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")