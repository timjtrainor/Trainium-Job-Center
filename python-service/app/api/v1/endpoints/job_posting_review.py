"""Endpoints for analyzing job posting fit using CrewAI."""

from typing import Any, Dict

from fastapi import APIRouter

from ....schemas.responses import StandardResponse, create_success_response, create_error_response
from ....services.crewai import get_job_review_crew

router = APIRouter()


@router.post("/jobs/posting/fit_review", response_model=StandardResponse)
async def job_posting_fit_review(job_data: Dict[str, Any]) -> StandardResponse:
    """Review a job posting and return fit analysis."""
    try:
        crew = get_job_review_crew()
        result = crew.job_review().kickoff(inputs={"job": job_data})
        
        # Wrap the result in StandardResponse format
        return create_success_response(
            data=result.raw,
            message="Job posting analysis completed successfully"
        )
    except Exception as e:
        # Return error in standard format
        error_data = {
            "job_id": job_data.get("id", "unknown"),
            "correlation_id": None,
            "final": {
                "recommend": False,
                "rationale": f"Analysis failed: {str(e)}",
                "confidence": "low"
            },
            "personas": [{
                "id": "error_handler",
                "recommend": False,
                "reason": f"Crew execution failed: {str(e)}"
            }],
            "tradeoffs": [],
            "actions": [
                "Review crew configuration",
                "Check system dependencies"
            ],
            "sources": ["error_handler"]
        }
        
        return create_success_response(
            data=error_data,
            message="Job posting analysis completed successfully"
        )
