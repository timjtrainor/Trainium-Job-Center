"""Routes for AI task queue management."""
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import get_queue_service, get_database_service
from ..services.infrastructure.queue import QueueService
from ..services.infrastructure.database import DatabaseService


class ResumeTailoringRequest(BaseModel):
    application_id: str = Field(..., description="Application identifier")
    job_description: str = Field(..., description="Full job description text")
    resume_json: Dict[str, Any] = Field(..., description="Base resume JSON payload")
    resume_summary: str = Field("", description="Resume summary paragraph")
    company_context: Dict[str, Any] = Field(default_factory=dict)
    narrative: Dict[str, Any] = Field(default_factory=dict)
    job_analysis: Optional[Dict[str, Any]] = Field(default=None)


class CompanyResearchRequest(BaseModel):
    company_id: Optional[str] = Field(None, description="Company identifier if available")
    company_name: str = Field(..., description="Company name to research")
    homepage_url: Optional[str] = Field(None, description="Company homepage URL")


class TaskEnqueueResponse(BaseModel):
    run_id: str
    task_id: str
    status: str = Field("queued")


class TaskRunStatusResponse(BaseModel):
    run_id: str
    task_type: str
    status: str
    trigger: str
    reference_id: Optional[str]
    schedule_id: Optional[str]
    task_id: Optional[str]
    started_at: Optional[str]
    finished_at: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    result: Optional[Any]
    error: Optional[str]


router = APIRouter(prefix="/tasks", tags=["AI Tasks"])


@router.post("/resume-tailoring", response_model=TaskEnqueueResponse)
async def enqueue_resume_tailoring(
    request: ResumeTailoringRequest,
    queue_service: QueueService = Depends(get_queue_service),
    db_service: DatabaseService = Depends(get_database_service),
) -> TaskEnqueueResponse:
    if not queue_service.initialized:
        await queue_service.initialize()
    if not db_service.initialized:
        await db_service.initialize()

    run_id = f"resume_{uuid4().hex[:8]}"

    await db_service.create_ai_task_run(
        run_id=run_id,
        task_type="resume_tailoring",
        trigger="manual",
        reference_id=request.application_id,
        payload=request.model_dump(),
    )

    job_info = queue_service.enqueue_resume_tailoring_job(
        application_id=request.application_id,
        payload=request.model_dump(),
        run_id=run_id,
        trigger="manual",
    )

    if not job_info:
        await db_service.update_ai_task_run(
            run_id,
            status="failed",
            error="Failed to enqueue resume tailoring job",
        )
        raise HTTPException(status_code=500, detail="Failed to enqueue resume tailoring job")

    await db_service.update_ai_task_run(
        run_id,
        status="queued",
        task_id=job_info["task_id"],
    )

    return TaskEnqueueResponse(run_id=run_id, task_id=job_info["task_id"])


@router.post("/company-research", response_model=TaskEnqueueResponse)
async def enqueue_company_research(
    request: CompanyResearchRequest,
    queue_service: QueueService = Depends(get_queue_service),
    db_service: DatabaseService = Depends(get_database_service),
) -> TaskEnqueueResponse:
    if not queue_service.initialized:
        await queue_service.initialize()
    if not db_service.initialized:
        await db_service.initialize()

    run_id = f"company_{uuid4().hex[:8]}"

    payload = {
        "company_id": request.company_id,
        "company_name": request.company_name,
        "homepage_url": request.homepage_url,
    }

    await db_service.create_ai_task_run(
        run_id=run_id,
        task_type="company_research",
        trigger="manual",
        reference_id=request.company_id,
        payload=payload,
    )

    job_info = queue_service.enqueue_company_research_job(
        company_id=request.company_id,
        payload=payload,
        run_id=run_id,
        trigger="manual",
    )

    if not job_info:
        await db_service.update_ai_task_run(
            run_id,
            status="failed",
            error="Failed to enqueue company research job",
        )
        raise HTTPException(status_code=500, detail="Failed to enqueue company research job")

    await db_service.update_ai_task_run(
        run_id,
        status="queued",
        task_id=job_info["task_id"],
    )

    return TaskEnqueueResponse(run_id=run_id, task_id=job_info["task_id"])


@router.get("/{run_id}", response_model=TaskRunStatusResponse)
async def get_task_run_status(
    run_id: str,
    queue_service: QueueService = Depends(get_queue_service),
    db_service: DatabaseService = Depends(get_database_service),
) -> TaskRunStatusResponse:
    if not db_service.initialized:
        await db_service.initialize()

    record = await db_service.get_ai_task_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task run not found")

    task_id = record.get("task_id") or run_id
    queue_status: Optional[Dict[str, Any]] = None

    if not queue_service.initialized:
        await queue_service.initialize()

    if task_id:
        queue_status = queue_service.get_job_status(task_id)

    result = record.get("result")
    if not result and queue_status and queue_status.get("result"):
        result = queue_status.get("result")

    return TaskRunStatusResponse(
        run_id=record["run_id"],
        task_type=record.get("task_type", "unknown"),
        status=record.get("status", "unknown"),
        trigger=record.get("trigger", "manual"),
        reference_id=record.get("reference_id"),
        schedule_id=record.get("schedule_id"),
        task_id=record.get("task_id"),
        started_at=(record.get("started_at").isoformat() if record.get("started_at") else None),
        finished_at=(record.get("finished_at").isoformat() if record.get("finished_at") else None),
        created_at=(record.get("created_at").isoformat() if record.get("created_at") else None),
        updated_at=(record.get("updated_at").isoformat() if record.get("updated_at") else None),
        result=result,
        error=record.get("error"),
    )
