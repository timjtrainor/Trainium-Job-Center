"""
API endpoints for job posting review CrewAI functionality.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from ....schemas.responses import StandardResponse, create_success_response, create_error_response
from ....services.crewai.job_posting_review.crew import get_job_posting_review_crew

router = APIRouter(prefix="/job-posting-review", tags=["Job Posting Review"])


@router.post("/analyze", response_model=StandardResponse)
async def analyze_job_posting(
    job_posting: Dict[str, Any]
):
    """
    Analyze a job posting using the CrewAI job posting review system.
    
    This endpoint runs the orchestrated crew that performs:
    1. Job intake and parsing
    2. Pre-filtering based on requirements 
    3. Quick fit analysis
    4. Brand framework matching
    5. Final orchestration and recommendation
    
    Args:
        job_posting: Dictionary or string containing job posting information
    
    Returns:
        Analysis results from the CrewAI crew
    """
    try:
        crew = get_job_posting_review_crew()
        
        # Convert job posting to string for the crew input
        job_posting_str = job_posting if isinstance(job_posting, str) else str(job_posting)
        
        # Run the crew with the job posting
        result = crew.kickoff(inputs={"job_posting": job_posting_str})
        
        return create_success_response(
            data={"result": str(result)},
            message="Job posting analysis completed successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to analyze job posting: {str(e)}")
        return create_error_response(
            error="Job posting analysis failed",
            message=str(e)
        )


@router.get("/health", response_model=StandardResponse) 
async def health_check():
    """
    Health check for the job posting review CrewAI service.
    
    Returns:
        Service health status and crew information
    """
    try:
        crew = get_job_posting_review_crew()
        
        health_status = {
            "service": "JobPostingReviewCrew",
            "agents_count": len(crew.agents),
            "tasks_count": len(crew.tasks),
            "process": str(crew.process),
            "status": "healthy"
        }
        
        return create_success_response(
            data=health_status,
            message="Job posting review service is healthy"
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_error_response(
            error="Health check failed", 
            message=str(e)
        )