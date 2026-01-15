"""
Jobs API endpoints.

Provides REST API for accessing jobs and job reviews.
"""
import asyncio
import base64
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
from loguru import logger
from datetime import datetime

from uuid import UUID
from ....schemas.job_reviews import ReviewedJobsResponse, ReviewedJob, JobDetails, JobReviewData
from ....schemas.job_parsing import JobParseRequest, JobParseResponse
from ....schemas.jobspy import ScrapedJob
from ....services.infrastructure.database import get_database_service, DatabaseService
from ....services.infrastructure.job_persistence import persist_jobs
from ....services.ai.job_parser import JobParser
from ....services.infrastructure.webhooks import publish_webhook_event


router = APIRouter(prefix="/jobs", tags=["jobs"])


class OverrideRequest(BaseModel):
    """Request model for human override of AI recommendation."""
    override_recommend: bool
    override_comment: str
    skip_webhook: bool = False

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


class JobIngestRecord(ScrapedJob):
    """Extended job payload allowing encoded descriptions."""
    description_encoded: Optional[str] = Field(
        default=None,
        description="Base64-encoded job description; overrides plain description if provided"
    )

    class Config:
        extra = "ignore"


class JobIngestRequest(BaseModel):
    """Request payload for ingesting external job records."""
    site_name: str = Field(..., min_length=1, description="Source identifier or job board name")
    jobs: List[JobIngestRecord] = Field(..., min_items=1, description="List of job records to persist")

    @validator("jobs", each_item=True)
    def _validate_job(cls, job: JobIngestRecord):
        if not job.job_url:
            raise ValueError("job_url is required for each job")
        if not job.title:
            raise ValueError("title is required for each job")
        return job


class JobIngestSummary(BaseModel):
    inserted: int = 0
    skipped_duplicates: int = 0
    blocked_duplicates: int = 0
    errors: List[str] = Field(default_factory=list)


class JobIngestResponse(BaseModel):
    success: bool
    summary: JobIngestSummary


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
        valid_sort_fields = [
            "date_posted",
            "company",
            "title",
            "review_date",
            "recommendation",
            "overall_alignment_score"
        ]
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reviews/{job_id}", response_model=ReviewedJob)
async def get_job_review(
    job_id: str,
    db: DatabaseService = Depends(get_database)
):
    """
    Get detailed review for a specific job by ID.
    Includes both job details and AI/human review data.
    """
    try:
        # Get review data
        review_data = await db.get_job_review(job_id)
        if not review_data:
            raise HTTPException(
                status_code=404,
                detail=f"Job review not found for job_id: {job_id}"
            )
        
        # Get job details
        job_data = await db.get_job_by_id(job_id)
        if not job_data:
            raise HTTPException(
                status_code=404,
                detail=f"Job details not found for job_id: {job_id}"
            )
        
        # Map database fields to JobDetails schema fields
        mapped_job = {
            "job_id": str(job_data.get("id")),
            "title": job_data.get("title"),
            "company": job_data.get("company"),
            "location": job_data.get("location_city") or job_data.get("location_state"),
            "url": job_data.get("job_url"),
            "date_posted": job_data.get("date_posted"),
            "source": job_data.get("site"),
            "description": job_data.get("description"),
            "salary_min": job_data.get("min_amount"),
            "salary_max": job_data.get("max_amount"),
            "salary_currency": job_data.get("currency"),
            "is_remote": job_data.get("is_remote"),
            "normalized_title": job_data.get("normalized_title"),
            "normalized_company": job_data.get("normalized_company"),
            "track": job_data.get("track")
        }
        
        # review_data is already normalized by db.get_job_review helper
        return ReviewedJob(job=JobDetails(**mapped_job), review=JobReviewData(**review_data))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job review: {e}")
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
    - 400: Invalid job_id format (not a valid UUID)
    - 404: Job review not found for the given job_id
    - 500: Database connection error or other server errors
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
        response = OverrideResponse(
            id=str(result["id"]),
            job_id=str(result["job_id"]),  # Convert UUID to string
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
        
        # Lookup application_id
        application_id = None
        try:
            # Query job_applications table for an application associated with this job
            async with db.pool.acquire() as conn:
                app_row = await conn.fetchrow("""
                    SELECT job_application_id 
                    FROM job_applications 
                    WHERE source_job_id = $1
                    LIMIT 1
                """, UUID(job_id))
                if app_row:
                    application_id = str(app_row['job_application_id'])
                    logger.info(f"Found application {application_id} for job {job_id}")
        except Exception as app_lookup_err:
            # Non-critical error, just log it
            logger.error(f"Failed to lookup application ID for job {job_id}: {app_lookup_err}")

        # Trigger webhook ONLY if approved AND not skipped
        if request.override_recommend and not request.skip_webhook:
            try:
                # Fetch job details to ensure title and company are available
                job = await db.get_job(job_id)
                
                publish_webhook_event(
                    event_type="job_approved",
                    payload={
                        "job_id": job_id,
                        "application_id": application_id,
                        "approval_mode": "manual_override",
                        "title": job.get("title") if job else result.get("title"),
                        "company": job.get("company_name") or job.get("company") if job else result.get("company"),
                        "override_comment": request.override_comment
                    }
                )
            except Exception as webhook_err:
                logger.error(f"Failed to trigger webhook for job {job_id}: {webhook_err}")
            
        return response
        
    except ValueError as e:
        # Invalid job_id format - client error
        logger.warning(f"Invalid job_id format: {job_id}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        # Database or other server errors
        logger.error(f"Failed to override job review: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=JobIngestResponse)
async def ingest_jobs(request: JobIngestRequest):
    """
    Ingest externally sourced job records and persist them with deduplication.

    The payload should include a source `site_name` and a list of job objects.
    Each job must include at least `title`, `company`, and `job_url`. Records
    are normalized and passed through the existing persistence pipeline, which
    performs canonical-key deduplication and fingerprint checks.
    """
    try:
        normalized_jobs: List[dict] = []
        for job in request.jobs:
            job_data = job.model_dump()
            encoded_description = job_data.pop("description_encoded", None)
            if encoded_description:
                try:
                    decoded_bytes = base64.b64decode(encoded_description)
                    job_data["description"] = decoded_bytes.decode("utf-8")
                except Exception as decode_error:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid base64 description for job '{job.job_url}': {decode_error}"
                    ) from decode_error
            job_data.setdefault("site", request.site_name)
            normalized_jobs.append(job_data)

        summary_dict = await persist_jobs(records=normalized_jobs, site_name=request.site_name)
        summary = JobIngestSummary(**summary_dict)
        success = summary.inserted > 0 and not summary.errors

        return JobIngestResponse(success=success, summary=summary)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ingest jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse", response_model=JobParseResponse)
async def parse_job_description(request: JobParseRequest):
    """
    Parse a raw job description using AI to extract structured data.
    """
    try:
        parser = JobParser()
        # Run blocking parser in a separate thread to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, parser.parse_job_text, request.description)
        return result
    except Exception as e:
        logger.error(f"Error in parse_job_description: {e}")
        raise HTTPException(status_code=500, detail=str(e))
