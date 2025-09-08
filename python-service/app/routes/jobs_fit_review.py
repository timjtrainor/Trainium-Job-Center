"""
FastAPI routes for the job posting fit review pipeline.

This module provides HTTP endpoints for triggering and managing
the CrewAI-powered job posting fit review process.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger

from ..models.job_posting import JobPosting
from ..models.fit_review import FitReviewResult
from ..services.fit_review import FitReviewOrchestrator

router = APIRouter(prefix="/jobs", tags=["Job Fit Review"])


@router.post("/fit-review", response_model=FitReviewResult)
async def evaluate_job_fit(
    job_posting: JobPosting,
    options: Optional[Dict[str, Any]] = None
) -> FitReviewResult:
    """
    Evaluate a job posting for fit using the CrewAI pipeline.
    
    This endpoint orchestrates the complete fit review process:
    1. Normalizes the job posting data
    2. Runs persona evaluations in parallel
    3. Aggregates results through the judge
    4. Returns comprehensive fit assessment
    
    Args:
        job_posting: The job posting to evaluate
        options: Optional configuration parameters
        
    Returns:
        Complete fit review result with recommendations
        
    Raises:
        HTTPException: If evaluation fails
    """
    try:
        logger.info(f"Received fit review request for: {job_posting.title} at {job_posting.company}")
        
        # Initialize orchestrator
        orchestrator = FitReviewOrchestrator()
        
        # Run the fit review pipeline
        result = await orchestrator.run(job_posting, options)
        
        logger.info(f"Fit review completed successfully for job: {result.job_id}")
        return result
        
    except Exception as e:
        logger.error(f"Fit review failed for {job_posting.title}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Job fit evaluation failed: {str(e)}"
        )


@router.post("/fit-review/async")
async def evaluate_job_fit_async(
    job_posting: JobPosting,
    background_tasks: BackgroundTasks,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Start asynchronous job fit evaluation.
    
    This endpoint starts the fit review process in the background
    and returns immediately with a job ID for tracking.
    
    Args:
        job_posting: The job posting to evaluate
        background_tasks: FastAPI background tasks
        options: Optional configuration parameters
        
    Returns:
        Dictionary with job_id for tracking the evaluation
    """
    job_id = f"job_{hash(job_posting.url)}"
    
    logger.info(f"Starting async fit review for job: {job_id}")
    
    async def run_fit_review():
        """Background task to run the fit review."""
        try:
            orchestrator = FitReviewOrchestrator()
            result = await orchestrator.run(job_posting, options)
            logger.info(f"Async fit review completed for job: {job_id}")
            # TODO: Store result in database or cache for retrieval
        except Exception as e:
            logger.error(f"Async fit review failed for job {job_id}: {str(e)}")
    
    background_tasks.add_task(run_fit_review)
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": "Fit review started in background"
    }


@router.get("/fit-review/{job_id}")
async def get_fit_review_result(job_id: str) -> Dict[str, Any]:
    """
    Retrieve the result of an asynchronous fit review.
    
    Args:
        job_id: The job ID returned from the async endpoint
        
    Returns:
        Fit review result or status information
    """
    # TODO: Implement result retrieval from database/cache
    logger.info(f"Retrieving fit review result for job: {job_id}")
    
    # Placeholder response
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Result retrieval not yet implemented"
    }