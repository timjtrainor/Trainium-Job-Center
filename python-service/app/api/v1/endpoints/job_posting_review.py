"""Endpoints for analyzing job posting fit using CrewAI."""

from typing import Any, Dict

from fastapi import APIRouter

from ....schemas.responses import StandardResponse, create_success_response
from ....services.crewai import get_job_review_crew

router = APIRouter()


@router.post("/jobs/posting/fit_review", response_model=StandardResponse)
async def job_posting_fit_review(job_data: Dict[str, Any]) -> StandardResponse:
    """Review a job posting and return fit analysis."""
    result = get_job_review_crew().job_review().kickoff(inputs={"job": job_data})
    return create_success_response(data=result.raw)
