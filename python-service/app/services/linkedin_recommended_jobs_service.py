"""Service for LinkedIn recommended jobs functionality."""

from typing import Dict, Any, List
from loguru import logger

from ..schemas.job_posting import LinkedInRecommendedJobsResponse, JobPosting

# Defensive import with graceful fallback
try:
    from .crewai.linkedin_recommended_jobs import run_linkedin_recommended_jobs
    LINKEDIN_CREW_AVAILABLE = True
except ImportError as e:
    LINKEDIN_CREW_AVAILABLE = False
    _import_error = str(e)
    logger.warning(f"LinkedIn recommended jobs crew not available: {e}")
    
    def run_linkedin_recommended_jobs() -> Dict[str, Any]:
        return {
            "success": False,
            "error_message": f"LinkedIn recommended jobs crew not available: {_import_error}"
        }


def fetch_linkedin_recommended_jobs() -> LinkedInRecommendedJobsResponse:
    """
    Fetch and normalize LinkedIn recommended jobs using the CrewAI crew.
    
    Returns:
        LinkedInRecommendedJobsResponse with job postings and metadata
    """
    # Check if crew is available
    if not LINKEDIN_CREW_AVAILABLE:
        logger.error("LinkedIn recommended jobs crew is not available")
        return LinkedInRecommendedJobsResponse(
            success=False,
            error_message="LinkedIn recommended jobs functionality is not available. Please ensure CrewAI dependencies are installed."
        )
    
    try:
        logger.info("Starting LinkedIn recommended jobs fetch")
        
        # Execute the CrewAI workflow
        result = run_linkedin_recommended_jobs()
        
        if not result:
            logger.warning("No result returned from LinkedIn recommended jobs crew")
            return LinkedInRecommendedJobsResponse(
                success=False,
                error_message="No result returned from job recommendation service"
            )
        
        # Check if the operation was successful
        success = result.get("success", False)
        
        if not success:
            error_msg = result.get("error_message", "Unknown error occurred")
            logger.error(f"LinkedIn recommended jobs crew failed: {error_msg}")
            return LinkedInRecommendedJobsResponse(
                success=False,
                error_message=error_msg
            )
        
        # Extract job postings from the result
        job_data = result.get("data", [])
        if not isinstance(job_data, list):
            logger.warning(f"Expected list of job postings, got: {type(job_data)}")
            job_data = []
        
        # Parse job postings
        job_postings = []
        for job_dict in job_data:
            try:
                if isinstance(job_dict, dict):
                    # Validate required fields
                    required_fields = ["title", "company", "location", "description", "url"]
                    missing_fields = [field for field in required_fields if field not in job_dict]
                    
                    if missing_fields:
                        logger.warning(f"Job posting missing fields {missing_fields}: {job_dict}")
                        continue
                    
                    job_posting = JobPosting(**job_dict)
                    job_postings.append(job_posting)
                else:
                    logger.warning(f"Expected dict for job posting, got: {type(job_dict)}")
            except Exception as e:
                logger.error(f"Failed to parse job posting {job_dict}: {e}")
                continue
        
        # Extract metadata
        metadata = {
            "processing_time": result.get("processing_time"),
            "crew_version": "1.0.0",
            "mcp_tools_used": ["get_recommended_jobs", "get_job_details"]
        }
        
        # Add any additional metadata from the result
        if "metadata" in result:
            metadata.update(result["metadata"])
        
        logger.info(f"Successfully processed {len(job_postings)} job postings")
        
        return LinkedInRecommendedJobsResponse(
            success=True,
            job_postings=job_postings,
            total_count=len(job_postings),
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error fetching LinkedIn recommended jobs: {e}")
        return LinkedInRecommendedJobsResponse(
            success=False,
            error_message=f"Internal service error: {str(e)}"
        )