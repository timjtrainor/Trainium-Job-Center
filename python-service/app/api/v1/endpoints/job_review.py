"""
Job Review API endpoints.

Provides REST API for managing job reviews.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from loguru import logger

from ....services.infrastructure.job_review_service import get_job_review_service


router = APIRouter(prefix="/job-review", tags=["job-review"])


class QueueJobsRequest(BaseModel):
    """Request model for queuing jobs."""
    limit: int = 50
    max_retries: int = 3


class QueueJobsResponse(BaseModel):
    """Response model for queue operation."""
    status: str
    queued_count: int
    failed_count: int
    message: str


class JobReviewStatusResponse(BaseModel):
    """Response model for job review status."""
    job_id: str
    job_title: Optional[str]
    job_company: Optional[str]
    job_status: str
    review_exists: bool
    review_data: Optional[Dict[str, Any]]


class ReviewStatsResponse(BaseModel):
    """Response model for review statistics."""
    job_status_counts: Dict[str, int]
    review_stats: Dict[str, Any]
    queue_info: Dict[str, Any]


async def get_service():
    """Dependency to get initialized job review service."""
    service = get_job_review_service()
    if not service.initialized:
        await service.initialize()
    return service


@router.post("/queue", response_model=QueueJobsResponse)
async def queue_pending_jobs(
    request: QueueJobsRequest,
    service = Depends(get_service)
):
    """Queue pending jobs for review."""
    try:
        result = await service.queue_pending_jobs(request.limit, request.max_retries)
        return QueueJobsResponse(**result)
    except Exception as e:
        logger.error(f"Failed to queue jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobReviewStatusResponse)
async def get_job_review_status(
    job_id: str,
    service = Depends(get_service)
):
    """Get review status for a specific job."""
    try:
        result = await service.get_review_status(job_id)
        if not result:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobReviewStatusResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_statistics(service = Depends(get_service)):
    """Get overall review statistics."""
    try:
        result = await service.get_review_stats()
        return ReviewStatsResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get review stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/requeue")
async def requeue_failed_jobs(
    max_retries: int = Query(3, description="Maximum retry attempts"),
    service = Depends(get_service)
):
    """Re-queue failed jobs for review."""
    try:
        result = await service.requeue_failed_jobs(max_retries)
        return result
    except Exception as e:
        logger.error(f"Failed to requeue jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/{job_id}")
async def test_job_review(
    job_id: str,
    service = Depends(get_service)
):
    """Queue a specific job for review (for testing)."""
    try:
        # Use the queue service directly for single job testing
        queue_service = service.queue_service
        
        task_id = queue_service.enqueue_job_review(job_id)
        if not task_id:
            raise HTTPException(status_code=500, detail="Failed to queue job")
        
        return {
            "status": "success",
            "job_id": job_id,
            "task_id": task_id,
            "message": f"Job {job_id} queued for review"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test job review: {e}")
        raise HTTPException(status_code=500, detail=str(e))