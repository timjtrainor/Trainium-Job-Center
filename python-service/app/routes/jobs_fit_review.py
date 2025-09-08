"""
FastAPI routes for the job posting fit review pipeline.

This module serves as a thin HTTP access point for the YAML-configured 
CrewAI pipeline, delegating execution entirely through run_crew.
"""
import time
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from loguru import logger

from ..models.job_posting import JobPosting
from ..models.fit_review import FitReviewResult
from ..services.crewai.job_posting_review.crew import run_crew

router = APIRouter(prefix="/jobs/posting", tags=["Job Posting Fit Review"])


@router.post("/fit_review", response_model=FitReviewResult)
async def evaluate_job_posting_fit(
    job_posting: JobPosting,
    options: Optional[Dict[str, Any]] = None
) -> FitReviewResult:
    """
    Evaluate a job posting for fit using the YAML-defined CrewAI pipeline.
    
    This endpoint delegates execution entirely to the YAML-configured crew,
    with no hardcoded orchestration logic. All business logic and persona
    coordination is defined via agents.yaml and tasks.yaml.
    
    Example Request:
    ```json
    {
        "title": "Senior Python Developer",
        "company": "Tech Innovations Inc",
        "location": "San Francisco, CA",
        "description": "We are looking for a senior Python developer...",
        "url": "https://example.com/jobs/senior-python-dev"
    }
    ```
    
    Example Response:
    ```json
    {
        "job_id": "job_123",
        "final": {
            "recommend": true,
            "rationale": "Strong overall fit with minor compensation concerns",
            "confidence": "high"
        },
        "personas": [
            {
                "id": "technical_leader",
                "recommend": true,
                "reason": "Excellent technical opportunities"
            }
        ],
        "tradeoffs": ["Lower salary but better equity potential"],
        "actions": ["Negotiate base salary", "Clarify equity terms"],
        "sources": ["company_website", "glassdoor"]
    }
    ```
    
    Args:
        job_posting: The job posting to evaluate
        options: Optional configuration parameters
        
    Returns:
        Complete fit review result with recommendations
        
    Raises:
        HTTPException: If evaluation fails
    """
    # Generate correlation ID for request tracking
    correlation_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Log route entry
    logger.info(
        f"POST /jobs/posting/fit_review - Request received",
        extra={
            "correlation_id": correlation_id,
            "route_path": "/jobs/posting/fit_review",
            "job_title": job_posting.title,
            "job_company": job_posting.company
        }
    )
    
    try:
        # Delegate execution entirely to YAML-defined crew
        result = run_crew(
            job_posting.model_dump(),
            options=options,
            correlation_id=correlation_id
        )
        
        # Calculate elapsed time
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Log route exit
        logger.info(
            f"POST /jobs/posting/fit_review - Request completed successfully",
            extra={
                "correlation_id": correlation_id,
                "route_path": "/jobs/posting/fit_review",
                "elapsed_time_ms": elapsed_ms,
                "recommendation": result.get("final", {}).get("recommend")
            }
        )
        
        # Convert dict result to Pydantic model
        return FitReviewResult.model_validate(result)
        
    except Exception as e:
        # Calculate elapsed time for error case
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Log error with correlation ID
        logger.error(
            f"POST /jobs/posting/fit_review - Request failed: {str(e)}",
            extra={
                "correlation_id": correlation_id,
                "route_path": "/jobs/posting/fit_review",
                "elapsed_time_ms": elapsed_ms,
                "job_title": job_posting.title,
                "job_company": job_posting.company
            }
        )
        
        # Return structured error response with correlation ID
        raise HTTPException(
            status_code=500,
            detail={
                "error": "fit_review_failed",
                "correlation_id": correlation_id
            }
        )
