"""LinkedIn recommended jobs API endpoints."""

from fastapi import APIRouter, HTTPException
from loguru import logger

# Defensive imports with graceful fallback
try:
    from ....schemas.job_posting import (
        LinkedInRecommendedJobsRequest,
        LinkedInRecommendedJobsResponse
    )
    SCHEMAS_AVAILABLE = True
except ImportError as e:
    SCHEMAS_AVAILABLE = False
    logger.warning(f"JobPosting schemas not available: {e}")
    # Create fallback classes
    class LinkedInRecommendedJobsRequest:
        pass
    class LinkedInRecommendedJobsResponse:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

try:
    from ....services.linkedin_recommended_jobs_service import fetch_linkedin_recommended_jobs
    SERVICE_AVAILABLE = True
except ImportError as e:
    SERVICE_AVAILABLE = False
    logger.warning(f"LinkedIn recommended jobs service not available: {e}")
    
    def fetch_linkedin_recommended_jobs():
        return LinkedInRecommendedJobsResponse(
            success=False,
            error_message="LinkedIn recommended jobs service is not available"
        )

router = APIRouter(prefix="/linkedin-recommended-jobs", tags=["LinkedIn Recommended Jobs"])


@router.post("/fetch", response_model=LinkedInRecommendedJobsResponse)
async def fetch_recommended_jobs(request: LinkedInRecommendedJobsRequest):
    """
    Fetch personalized LinkedIn job recommendations for the current user.
    
    This endpoint uses the MCP Gateway to:
    1. Fetch recommended job IDs from LinkedIn for the logged-in user
    2. Retrieve detailed job information for each recommendation
    3. Normalize the data to the standard JobPosting schema
    
    Note: This endpoint does NOT perform any recommendation logic, filtering,
    ranking, or job fit evaluation. It only retrieves and normalizes data.
    
    Returns:
        LinkedInRecommendedJobsResponse: Contains list of normalized job postings
    """
    # Check if dependencies are available
    if not SCHEMAS_AVAILABLE or not SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LinkedIn recommended jobs functionality is not available. Dependencies not installed."
        )
    
    try:
        logger.info("Received request for LinkedIn recommended jobs")
        
        # Fetch recommended jobs using the service
        result = fetch_linkedin_recommended_jobs()
        
        if not result.success:
            # Return error response with appropriate HTTP status
            if "service error" in (result.error_message or "").lower():
                raise HTTPException(status_code=500, detail=result.error_message)
            else:
                raise HTTPException(status_code=502, detail=result.error_message)
        
        logger.info(f"Successfully fetched {result.total_count} recommended jobs")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in LinkedIn recommended jobs endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health", response_model=dict)
async def health_check():
    """
    Health check endpoint for LinkedIn recommended jobs service.
    
    Returns:
        dict: Service health status and configuration info
    """
    try:
        # Basic health check - verify the service can be imported
        from ....services.linkedin_recommended_jobs_service import fetch_linkedin_recommended_jobs
        
        return {
            "status": "healthy",
            "service": "linkedin-recommended-jobs",
            "version": "1.0.0",
            "description": "LinkedIn job recommendations fetching and normalization service",
            "mcp_tools": ["get_recommended_jobs", "get_job_details"],
            "output_schema": ["title", "company", "location", "description", "url"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )