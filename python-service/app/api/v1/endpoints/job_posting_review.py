"""Job Posting Review API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from loguru import logger

from ....schemas.job_posting_review import JobPostingReviewRequest, JobPostingReviewResponse
from ....schemas.responses import create_success_response, create_error_response
from ....services.crewai.job_posting_review import get_job_posting_review_crew


router = APIRouter(prefix="/job-posting-review", tags=["Job Posting Review"])


@router.post("", response_model=Dict[str, Any])
async def analyze_job_posting(request: JobPostingReviewRequest):
    """
    Analyze job posting fit against career brand framework using company research data.
    
    This endpoint evaluates job postings across multiple dimensions:
    - Skills and requirements alignment
    - Cultural fit and values alignment
    - Compensation competitiveness
    - Career growth potential
    
    Returns comprehensive fit evaluation with recommendations and specific actions.
    """
    try:
        logger.info(f"Starting job posting review for {request.job_posting.company} - {request.job_posting.title}")
        
        # Get the job posting review crew
        crew = get_job_posting_review_crew()
        
        # Prepare inputs for the crew
        inputs = {
            "job_title": request.job_posting.title,
            "company_name": request.job_posting.company,
            "job_location": request.job_posting.location or "",
            "job_description": request.job_posting.description,
            "company_research": request.company_research or {},
            "options": request.options
        }
        
        # Execute the crew analysis
        result = crew.kickoff(inputs=inputs)
        
        # Extract the result data
        if hasattr(result, 'raw'):
            result_data = result.raw
        else:
            result_data = result
            
        # Parse the result if it's a string
        if isinstance(result_data, str):
            import json
            try:
                result_data = json.loads(result_data)
            except json.JSONDecodeError:
                # Try to extract JSON from the string
                import re
                json_match = re.search(r'\{.*\}', result_data, re.DOTALL)
                if json_match:
                    result_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse crew result as JSON")
        
        logger.info(f"Job posting review completed successfully for {request.job_posting.company}")
        
        return create_success_response(
            data=result_data,
            message="Job posting review completed successfully"
        )
        
    except ValueError as e:
        logger.error(f"Job posting review validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
        
    except Exception as e:
        logger.error(f"Job posting review failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Job posting review failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for the job posting review service."""
    try:
        # Test crew initialization
        crew = get_job_posting_review_crew()
        
        return create_success_response(
            data={
                "service": "job_posting_review",
                "status": "healthy",
                "agents_count": len(crew.agents),
                "tasks_count": len(crew.tasks)
            },
            message="Job posting review service is healthy"
        )
        
    except Exception as e:
        logger.error(f"Job posting review health check failed: {str(e)}")
        return create_error_response(
            error=f"Health check failed: {str(e)}",
            message="Job posting review service is unhealthy"
        )