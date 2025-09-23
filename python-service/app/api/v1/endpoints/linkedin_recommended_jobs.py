"""API endpoints for LinkedIn recommended jobs."""

from __future__ import annotations

from fastapi import APIRouter
from loguru import logger

from ....schemas.linkedin_recommended_jobs import LinkedInRecommendedJobsResponse
from ....schemas.responses import (
    StandardResponse,
    create_error_response,
    create_success_response,
)
from ....services.crewai.linkedin_recommended_jobs.crew import (
    run_linkedin_recommended_jobs,
)

router = APIRouter(
    prefix="/linkedin-recommended-jobs",
    tags=["LinkedIn Recommended Jobs"],
)


@router.post("", response_model=StandardResponse)
async def generate_linkedin_recommended_jobs() -> StandardResponse:
    """Run the LinkedIn recommended jobs crew."""

    try:
        result = run_linkedin_recommended_jobs()

        success_flag = bool(result.get("success", True))
        error_message = result.get("error")
        if not success_flag or error_message:
            message = error_message or "Unknown error occurred"
            return create_error_response(
                error="LinkedIn recommended jobs failed",
                message=message,
                data={k: v for k, v in result.items() if k not in {"success", "error"}},
            )

        response_payload = LinkedInRecommendedJobsResponse(
            success=True,
            recommended_jobs=result.get("recommended_jobs", []),
            metadata=result.get("metadata", {}),
            summary=result.get("summary"),
        )
        return create_success_response(
            data=response_payload.model_dump(),
            message="LinkedIn recommended jobs generated successfully",
        )
    except Exception as exc:
        logger.error("LinkedIn recommended jobs API error: {}", exc)
        return create_error_response(
            error="LinkedIn recommended jobs failed",
            message=str(exc),
        )
