"""API endpoints for LinkedIn recommended jobs."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from loguru import logger

from ....schemas.linkedin_recommended_jobs import (
    LinkedInRecommendedJobsRequest,
    LinkedInRecommendedJobsResponse,
)
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


def _build_inputs(request: LinkedInRecommendedJobsRequest) -> Dict[str, Any]:
    """Convert the request model into crew input payload without profile URL."""

    inputs: Dict[str, Any] = {
        "user_id": request.user_id,
        "limit": request.limit,
        "job_preferences": request.job_preferences,
        "target_companies": request.target_companies,
        "location_preferences": request.location_preferences,
        "include_remote": request.include_remote,
        "notes": request.notes,
    }

    return {key: value for key, value in inputs.items() if value is not None}


@router.post("", response_model=StandardResponse)
async def generate_linkedin_recommended_jobs(
    request: LinkedInRecommendedJobsRequest,
) -> StandardResponse:
    """Run the LinkedIn recommended jobs crew."""

    try:
        profile_url: Optional[str] = (
            str(request.profile_url) if request.profile_url else None
        )
        if not profile_url:
            logger.info(
                "LinkedIn recommended jobs request missing profile URL; continuing without it.",
            )

        crew_inputs = _build_inputs(request)
        result = run_linkedin_recommended_jobs(crew_inputs, profile_url=profile_url)

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
