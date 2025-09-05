"""API endpoint for personal brand job review."""
from typing import Dict, Any
from fastapi import APIRouter
from loguru import logger

from ..models.responses import (
    StandardResponse,
    create_success_response,
    create_error_response,
)
from ..services.crewai_personal_brand import PersonalBrandCrew

router = APIRouter()


@router.post("/personal-brand", response_model=StandardResponse)
async def review_job_posting(job_data: Dict[str, Any]):
    """Analyze a job posting using the personal brand crew."""
    try:
        crew = PersonalBrandCrew()
        result = crew.personal_brand().kickoff(inputs={"job": job_data})
        return create_success_response(data=result, message="Job analysis completed")
    except Exception as e:
        logger.error(f"Failed to review job posting: {e}")
        return create_error_response(
            error="Failed to analyze job", message=str(e)
        )

