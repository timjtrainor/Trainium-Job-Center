"""FastAPI endpoint for the LinkedIn recommended jobs CrewAI service."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type, TypeVar

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ValidationError
from structlog.contextvars import bind_contextvars, clear_contextvars
from structlog.typing import FilteringBoundLogger

from ....core.config import get_settings
from ....schemas.linkedin_recommended_jobs import (
    LinkedInEnrichedJobDetail,
    LinkedInRecommendedJobSummary,
    LinkedInRecommendedJobsResult,
)
from ....services.crewai.linkedin_recommended_jobs.crew import (
    LinkedInRecommendedJobsCrew,
    normalize_linkedin_recommended_jobs_output,
    write_recommended_job_outputs,
)
from ....services.crewai.linkedin_recommended_jobs.exceptions import (
    CrewExecutionError,
    LinkedInRecommendedJobsError,
    MCPConnectionError,
    ToolExecutionError,
)
from ....services.crewai.tools.mcp_tools import MCPToolsManager, MCPToolsManagerError


_LOGGER = structlog.get_logger(__name__)
_STRUCTLOG_CONFIGURED = False
_ModelT = TypeVar("_ModelT", bound=BaseModel)

router = APIRouter(prefix="/linkedin-recommended-jobs", tags=["LinkedIn Recommended Jobs"])


def _ensure_structlog_configured() -> None:
    """Configure structlog once for JSON-formatted logs."""

    global _STRUCTLOG_CONFIGURED
    if _STRUCTLOG_CONFIGURED:
        return

    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )
    _STRUCTLOG_CONFIGURED = True


def _http_error(
    *,
    status_code: int,
    error: str,
    message: str,
    request_id: str,
    details: Optional[Dict[str, Any]] = None,
) -> HTTPException:
    payload: Dict[str, Any] = {
        "error": error,
        "message": message,
        "request_id": request_id,
    }
    if details:
        payload["details"] = details
    return HTTPException(status_code=status_code, detail=payload)


def _build_inputs(settings) -> Dict[str, Any]:
    return {
        key: value
        for key, value in {
            "profile_url": settings.linkedin_recommended_profile_url,
            "location": settings.linkedin_recommended_location,
            "keywords": settings.linkedin_recommended_keywords,
            "limit": settings.linkedin_recommended_limit,
            "job_preferences": settings.linkedin_recommended_job_preferences,
        }.items()
        if value is not None and value != ""
    }


def _log_and_raise_missing_profile(request_id: str) -> None:
    message = "LinkedIn recommended profile URL is not configured"
    _LOGGER.error(
        "linkedin_recommended_jobs_configuration_missing",
        request_id=request_id,
        message=message,
    )
    raise _http_error(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="CrewExecutionError",
        message=message,
        request_id=request_id,
    )


def _parse_job_items(
    items: Any,
    *,
    model: Type[_ModelT],
    event_name: str,
    request_id: str,
    log: FilteringBoundLogger,
) -> List[_ModelT]:
    parsed: List[_ModelT] = []
    invalid_entries = 0

    if not isinstance(items, Sequence) or isinstance(items, (str, bytes, bytearray)):
        return parsed

    for entry in items:
        if not isinstance(entry, Mapping):
            invalid_entries += 1
            continue
        try:
            parsed.append(model.model_validate(entry))
        except ValidationError as exc:
            invalid_entries += 1
            log.warning(
                event_name,
                request_id=request_id,
                error=str(exc),
                error_type=exc.__class__.__name__,
                entry_keys=list(entry.keys()),
            )

    if invalid_entries:
        if parsed:
            log.warning(
                f"{event_name}_partial_success",
                request_id=request_id,
                invalid_entries=invalid_entries,
                parsed_entries=len(parsed),
            )
        else:
            log.error(
                f"{event_name}_invalid_payload",
                request_id=request_id,
                invalid_entries=invalid_entries,
                model=model.__name__,
            )
            raise CrewExecutionError(
                "Crew returned invalid job payloads",
                request_id=request_id,
                details={
                    "error_category": "validation",
                    "invalid_entries": invalid_entries,
                    "model": model.__name__,
                },
            )

    return parsed


def _status_for_exception(exc: LinkedInRecommendedJobsError) -> int:
    if isinstance(exc, CrewExecutionError) and exc.details.get("error_category") == "validation":
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_500_INTERNAL_SERVER_ERROR


@router.post("", response_model=LinkedInRecommendedJobsResult)
async def run_linkedin_recommended_jobs() -> LinkedInRecommendedJobsResult:
    """Execute the LinkedIn recommended jobs crew and return structured results."""

    _ensure_structlog_configured()

    request_id = str(uuid.uuid4())
    bind_contextvars(request_id=request_id)
    log = _LOGGER.bind(request_id=request_id)

    log.info("linkedin_recommended_jobs_request_received")
    settings = get_settings()

    if not settings.linkedin_recommended_profile_url:
        _log_and_raise_missing_profile(request_id)

    inputs = _build_inputs(settings)
    log.info("linkedin_recommended_jobs_crew_inputs_prepared", input_keys=list(inputs.keys()))

    manager = MCPToolsManager()
    crew_service: Optional[LinkedInRecommendedJobsCrew] = None

    try:
        try:
            manager.connect()
        except MCPToolsManagerError as exc:
            log.error(
                "linkedin_recommended_jobs_mcp_connection_failed",
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
            raise MCPConnectionError("Failed to connect to MCP gateway", request_id=request_id) from exc

        crew_service = LinkedInRecommendedJobsCrew(tools_manager=manager)
        crew = crew_service.crew()

        log.info(
            "linkedin_recommended_jobs_crew_started",
            argument_keys=list(inputs.keys()),
        )
        start_time = time.perf_counter()
        try:
            raw_result = await asyncio.to_thread(crew.kickoff, inputs=inputs)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            log.exception(
                "linkedin_recommended_jobs_crew_failed",
                duration_ms=duration_ms,
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
            raise CrewExecutionError("LinkedIn recommended jobs crew execution failed", request_id=request_id) from exc
        else:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            log.info(
                "linkedin_recommended_jobs_crew_completed",
                duration_ms=duration_ms,
            )

        normalized = normalize_linkedin_recommended_jobs_output(raw_result)
        discovered_raw = normalized.get("discovered_jobs", [])
        enriched_raw = normalized.get("enriched_jobs", [])
        success_flag = bool(normalized.get("success", bool(enriched_raw or discovered_raw)))
        log.info(
            "linkedin_recommended_jobs_result_received",
            success=success_flag,
            discovered_count=len(discovered_raw) if isinstance(discovered_raw, Sequence) else 0,
            enriched_count=len(enriched_raw) if isinstance(enriched_raw, Sequence) else 0,
        )

        error_message = normalized.get("error") or (normalized.get("metadata") or {}).get("error")
        if not success_flag:
            log.error(
                "linkedin_recommended_jobs_tool_failure",
                error=error_message,
            )
            raise ToolExecutionError(
                error_message or "LinkedIn recommended jobs tools returned failure",
                request_id=request_id,
                details={"metadata": normalized.get("metadata")},
            )

        discovered = _parse_job_items(
            discovered_raw,
            model=LinkedInRecommendedJobSummary,
            event_name="linkedin_recommended_jobs_discovered_invalid",
            request_id=request_id,
            log=log,
        )
        enriched = _parse_job_items(
            enriched_raw,
            model=LinkedInEnrichedJobDetail,
            event_name="linkedin_recommended_jobs_enriched_invalid",
            request_id=request_id,
            log=log,
        )

        metadata = normalized.get("metadata")
        if isinstance(metadata, Mapping):
            metadata_payload = dict(metadata)
        else:
            metadata_payload = {}

        write_recommended_job_outputs(normalized)

        response = LinkedInRecommendedJobsResult(
            request_id=request_id,
            discovered_jobs=discovered,
            enriched_jobs=enriched,
            metadata=metadata_payload,
        )

        log.info(
            "linkedin_recommended_jobs_request_completed",
            discovered_count=len(discovered),
            enriched_count=len(enriched),
        )
        return response

    except LinkedInRecommendedJobsError as exc:
        status_code = _status_for_exception(exc)
        raise _http_error(
            status_code=status_code,
            error=exc.__class__.__name__,
            message=exc.message,
            request_id=request_id,
            details=exc.details or None,
        ) from exc
    finally:
        try:
            if crew_service is not None:
                crew_service.close()
            else:
                manager.close()
        finally:
            clear_contextvars()
