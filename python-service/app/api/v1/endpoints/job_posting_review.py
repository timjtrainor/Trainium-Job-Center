"""
API endpoints for job posting review CrewAI functionality.
"""
import uuid
from typing import Dict, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from pydantic import BaseModel, Field

from ....schemas.responses import StandardResponse, create_success_response, create_error_response
from ....services.fit_review.workflows.job_review_graph import run_job_review_workflow
from ....services.infrastructure.job_persistence import get_job_persistence_service
from ....services.infrastructure.database import get_database_service

router = APIRouter(prefix="/job-posting-review", tags=["Job Posting Review"])


class JobPostingInput(BaseModel):
    """Input model for job posting analysis."""
    job_posting: Union[str, Dict[str, Any]] = Field(
        ..., 
        description="Job posting as string or dictionary containing job details"
    )
    options: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional configuration parameters for the analysis"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_posting": {
                    "title": "Senior Machine Learning Engineer",
                    "company": "Acme Corp",
                    "description": "We are looking for a senior ML engineer...",
                    "location": "San Francisco, CA",
                    "salary": "$180,000 - $220,000"
                },
                "options": {
                    "detailed_analysis": True,
                    "include_market_research": False
                }
            }
        }


@router.post("/analyze", response_model=StandardResponse)
async def analyze_job_posting(job_input: JobPostingInput):
    """
    Analyze a job posting using the LangGraph job posting review system.
    """
    try:
        # Convert job posting to standardized format
        if isinstance(job_input.job_posting, str):
            job_data = {
                "title": "Manual Analysis",
                "company": "Unknown",
                "description": job_input.job_posting,
                "job_url": f"https://manual-analysis.job/{uuid.uuid4().hex[:8]}"
            }
        else:
            job_data = job_input.job_posting
            if "job_url" not in job_data:
                job_data["job_url"] = f"https://manual-analysis.job/{uuid.uuid4().hex[:8]}"
            
        # 1. Persist the job first (Standard requirement for our stateful graph)
        persistence_service = get_job_persistence_service()
        result = await persistence_service.persist_jobs([job_data], site_name="manual_upload")
        
        job_id = None
        if "inserted_job_ids" in result and result["inserted_job_ids"]:
            job_id = result["inserted_job_ids"][0]
        else:
            # Maybe it already exists? Try to find it by URL
            db_service = get_database_service()
            async with db_service.pool.acquire() as conn:
                job_id = await conn.fetchval(
                    "SELECT id FROM jobs WHERE job_url = $1 LIMIT 1",
                    job_data["job_url"]
                )
        
        if not job_id:
            raise HTTPException(status_code=500, detail="Failed to persist job for analysis")

        # 2. Check for Langflow Test Mode
        import os
        if os.getenv("LANGFLOW_TEST_MODE", "false").lower() == "true":
            logger.info(f"LANGFLOW_TEST_MODE enabled for API request. Job {job_id} redirected.")
            return create_success_response(
                data={"status": "testing", "job_id": str(job_id)},
                message="LANGFLOW_TEST_MODE detected. Job has been sent to Langflow for visual testing."
            )

        # 3. Run the graph workflow
        await run_job_review_workflow(job_id=str(job_id), user_id="api_request")

        # 3. Fetch the results from the DB
        db_service = get_database_service()
        review_result = await db_service.get_job_review(str(job_id))
        
        if not review_result:
             return create_success_response(
                data={"status": "processing", "job_id": str(job_id)},
                message="Analysis started. Please check back later."
            )
        
        return create_success_response(
            data=review_result,
            message="Job posting analysis completed successfully via LangGraph"
        )
    
    except Exception as e:
        logger.error(f"Failed to analyze job posting: {str(e)}")
        return create_error_response(
            error="Job posting analysis failed",
            message=str(e)
        )


@router.post("/analyze/simple", response_model=StandardResponse)
async def analyze_job_posting_simple(job_posting: Union[str, Dict[str, Any]]):
    """
    Simplified endpoint for job posting analysis.
    """
    job_input = JobPostingInput(job_posting=job_posting)
    return await analyze_job_posting(job_input)


@router.get("/health", response_model=StandardResponse) 
async def health_check():
    """
    Health check for the job posting review service.
    """
    return create_success_response(
        data={"status": "healthy", "engine": "LangGraph"},
        message="Job posting review service is healthy"
    )