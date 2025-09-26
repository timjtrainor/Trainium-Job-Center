"""
Jobs API endpoints.

Provides REST API for accessing jobs and job reviews.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from loguru import logger
from datetime import datetime

from ....schemas.job_reviews import ReviewedJobsResponse, ReviewedJob, JobDetails, JobReviewData
from ....services.infrastructure.database import get_database_service, DatabaseService


router = APIRouter(prefix="/jobs", tags=["jobs"])


class OverrideRequest(BaseModel):
    """Request model for human override of AI recommendation."""
    override_recommend: bool
    override_comment: str

    class Config:
        json_schema_extra = {
            "example": {
                "override_recommend": True,
                "override_comment": "Human reviewer approved despite low AI score - company culture is excellent match"
            }
        }


class OverrideResponse(BaseModel):
    """Response model for override operation."""
    id: str
    job_id: str
    recommend: Optional[bool]
    confidence: Optional[str]
    rationale: Optional[str]
    override_recommend: bool
    override_comment: str
    override_by: str
    override_at: str
    created_at: str
    updated_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "12345",
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "recommend": False,
                "confidence": "medium",
                "rationale": "AI identified some concerns about work-life balance",
                "override_recommend": True,
                "override_comment": "Human reviewer approved despite low AI score - company culture is excellent match",
                "override_by": "system_admin",
                "override_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-15T09:15:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


async def get_database():
    """Dependency to get initialized database service."""
    db_service = get_database_service()
    if not db_service.initialized:
        await db_service.initialize()
    return db_service


@router.get("/reviews", response_model=ReviewedJobsResponse)
async def get_job_reviews(
    limit: int = Query(50, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    sort_by: str = Query("date_posted", description="Sort field: date_posted, company, title, review_date, recommendation"),
    sort_order: str = Query("DESC", description="Sort order: ASC or DESC"),
    recommendation: Optional[bool] = Query(None, description="Filter by recommendation status"),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum alignment score"),
    max_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum alignment score"),
    company: Optional[str] = Query(None, description="Filter by company name (partial match)"),
    source: Optional[str] = Query(None, description="Filter by job source"),
    is_remote: Optional[bool] = Query(None, description="Filter by remote work availability"),
    date_posted_after: Optional[datetime] = Query(None, description="Filter jobs posted after this date"),
    date_posted_before: Optional[datetime] = Query(None, description="Filter jobs posted before this date"),
    db: DatabaseService = Depends(get_database)
):
    """
    Get reviewed job postings with combined job and review data.
    
    Returns paginated results with support for filtering and sorting.
    Combines data from jobs and job_reviews tables.
    """
    try:
        # Validate sort parameters
        valid_sort_fields = ["date_posted", "company", "title", "review_date", "recommendation"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"
            )
        
        if sort_order.upper() not in ["ASC", "DESC"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid sort_order. Must be ASC or DESC"
            )

        # Get data from database
        result = await db.get_reviewed_jobs(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            recommendation=recommendation,
            min_score=min_score,
            max_score=max_score,
            company=company,
            source=source,
            is_remote=is_remote,
            date_posted_after=date_posted_after,
            date_posted_before=date_posted_before
        )

        # Calculate pagination info
        page = (offset // limit) + 1
        total_count = result["total_count"]
        has_more = offset + limit < total_count

        # Transform to response models
        reviewed_jobs = []
        for job_data in result["jobs"]:
            job_details = JobDetails(**job_data["job"])
            review_data = JobReviewData(**job_data["review"])
            reviewed_job = ReviewedJob(job=job_details, review=review_data)
            reviewed_jobs.append(reviewed_job)

        return ReviewedJobsResponse(
            jobs=reviewed_jobs,
            total_count=total_count,
            page=page,
            page_size=limit,
            has_more=has_more
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job reviews: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reviews/{job_id}/override", response_model=OverrideResponse)
async def override_job_review(
    job_id: str,
    request: OverrideRequest,
    db: DatabaseService = Depends(get_database)
):
    """
    Override AI job recommendation with human decision.
    
    Allows human reviewers to override AI recommendations while preserving
    the original AI analysis. Updates the job review with override data.
    
    **Request Example:**
    ```json
    {
        "override_recommend": true,
        "override_comment": "Human reviewer approved despite low AI score"
    }
    ```
    
    **Response Example:**
    ```json
    {
        "id": "12345",
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "recommend": false,
        "confidence": "medium", 
        "rationale": "AI identified concerns about work-life balance",
        "override_recommend": true,
        "override_comment": "Human reviewer approved despite low AI score",
        "override_by": "system_admin",
        "override_at": "2024-01-15T10:30:00Z",
        "created_at": "2024-01-15T09:15:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
    ```
    
    **Features:**
    - Preserves original AI fields (recommend, confidence, rationale, etc.)
    - Adds human override data with timestamp and reviewer ID
    - Returns complete updated review record
    - Validates job_id exists before updating
    
    **Error Responses:**
    - 404: Job review not found for the given job_id
    - 500: Internal server error during update
    """
    try:
        # Update the job review with override data
        result = await db.update_job_review_override(
            job_id=job_id,
            override_recommend=request.override_recommend,
            override_comment=request.override_comment,
            override_by="system_admin"  # Placeholder until user auth exists
        )
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Job review not found for job_id: {job_id}"
            )
        
        # Transform the result to match the response model
        return OverrideResponse(
            id=str(result["id"]),
            job_id=result["job_id"],
            recommend=result["recommend"],
            confidence=result["confidence"],
            rationale=result["rationale"],
            override_recommend=result["override_recommend"],
            override_comment=result["override_comment"],
            override_by=result["override_by"],
            override_at=result["override_at"].isoformat() if result["override_at"] else None,
            created_at=result["created_at"].isoformat() if result["created_at"] else None,
            updated_at=result["updated_at"].isoformat() if result["updated_at"] else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to override job review: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))