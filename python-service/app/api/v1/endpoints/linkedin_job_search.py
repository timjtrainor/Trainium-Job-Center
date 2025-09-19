"""
API endpoints for LinkedIn Job Search CrewAI functionality.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from ....schemas.responses import StandardResponse, create_success_response, create_error_response
from ....schemas.linkedin_job_search import LinkedInJobSearchRequest, LinkedInJobSearchResponse
from ....services.crewai.linkedin_job_search.crew import (
    get_linkedin_job_search_crew,
    normalize_linkedin_job_search_output,
)

router = APIRouter(prefix="/linkedin-job-search", tags=["LinkedIn Job Search"])


def _format_search_criteria(request: LinkedInJobSearchRequest) -> str:
    """Generate a human readable description of the provided search parameters."""

    parts = [f"Keywords: '{request.keywords}'"]

    if request.location:
        parts.append(f"Location: {request.location}")

    filter_parts = []
    if request.remote:
        filter_parts.append("Remote only")
    if request.job_type:
        filter_parts.append(f"Job type: {request.job_type}")
    if request.date_posted:
        filter_parts.append(f"Date posted: {request.date_posted}")
    if request.experience_level:
        filter_parts.append(f"Experience level: {request.experience_level}")

    if filter_parts:
        parts.append("Filters: " + ", ".join(filter_parts))

    if request.limit is not None:
        parts.append(f"Limit: {request.limit}")

    return "; ".join(parts)


@router.post("/search", response_model=StandardResponse)
async def search_linkedin_jobs(request: LinkedInJobSearchRequest):
    """
    Execute parameterized LinkedIn job search with both search and recommendations.
    
    This endpoint uses CrewAI agents to:
    1. Search LinkedIn jobs with provided parameters
    2. Retrieve personalized job recommendations (if authenticated)
    3. Consolidate and deduplicate results
    4. Return structured job data suitable for database persistence
    
    Args:
        request: LinkedIn job search parameters
    
    Returns:
        Consolidated job search results with metadata
    """
    try:
        logger.info(f"Starting LinkedIn job search for keywords: '{request.keywords}'")
        
        # Convert request to search parameters
        search_criteria = _format_search_criteria(request)

        search_params = {
            "keywords": request.keywords,
            "location": request.location,
            "job_type": request.job_type,
            "date_posted": request.date_posted,
            "experience_level": request.experience_level,
            "remote": request.remote,
            "limit": request.limit,
            "search_criteria": search_criteria,
        }

        # Remove None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
        
        # Execute LinkedIn job search crew
        crew = get_linkedin_job_search_crew()
        result = crew.kickoff(inputs=search_params)
        result = normalize_linkedin_job_search_output(result)

        # Check if search was successful
        if not result.get("success", False):
            return create_error_response(
                error="LinkedIn job search failed",
                message=result.get("error", "Unknown error occurred")
            )

        # Transform result to response schema
        response_data = LinkedInJobSearchResponse(
            success=result.get("success", True),
            consolidated_jobs=result.get("consolidated_jobs", []),
            total_jobs=result.get("total_jobs", 0),
            search_jobs_count=result.get("search_jobs_count", 0),
            recommended_jobs_count=result.get("recommended_jobs_count", 0),
            duplicates_removed=result.get("duplicates_removed", 0),
            consolidation_metadata=result.get("consolidation_metadata", {}),
        )
        
        return create_success_response(
            data=response_data.model_dump(),
            message=f"LinkedIn job search completed: {response_data.total_jobs} jobs found"
        )
        
    except Exception as e:
        logger.error(f"LinkedIn job search API error: {str(e)}")
        return create_error_response(
            error="LinkedIn job search failed",
            message=str(e)
        )


@router.get("/health", response_model=StandardResponse)
async def health_check():
    """Health check for LinkedIn job search crew."""
    try:
        crew = get_linkedin_job_search_crew()
        
        # Basic health check - ensure crew can be instantiated
        health_data = {
            "crew_initialized": crew is not None,
            "linkedin_tools_loaded": len(crew._linkedin_tools) > 0 if hasattr(crew, '_linkedin_tools') else False,
            "agents_count": len(crew.agents) if crew else 0,
            "tasks_count": len(crew.tasks) if crew else 0
        }
        
        return create_success_response(
            data=health_data,
            message="LinkedIn job search crew is healthy"
        )
        
    except Exception as e:
        logger.error(f"LinkedIn job search health check failed: {str(e)}")
        return create_error_response(
            error="Health check failed",
            message=str(e)
        )


@router.get("/config", response_model=StandardResponse)
async def get_crew_config():
    """Get LinkedIn job search crew configuration details."""
    try:
        crew = get_linkedin_job_search_crew()
        
        config_data = {
            "crew_type": "linkedin_job_search",
            "process": "sequential", 
            "agents": [
                {"name": "search_agent", "role": "LinkedIn Job Search Specialist"},
                {"name": "recommendation_agent", "role": "LinkedIn Recommendations Specialist"},
                {"name": "orchestration_agent", "role": "LinkedIn Job Search Coordinator"}
            ],
            "tasks": [
                {"name": "search_jobs_task", "async": True},
                {"name": "get_recommendations_task", "async": True}, 
                {"name": "consolidate_results_task", "async": False}
            ],
            "linkedin_tools_available": len(crew._linkedin_tools) if hasattr(crew, '_linkedin_tools') else 0
        }
        
        return create_success_response(
            data=config_data,
            message="LinkedIn job search crew configuration retrieved"
        )
        
    except Exception as e:
        logger.error(f"Failed to get crew config: {str(e)}")
        return create_error_response(
            error="Configuration retrieval failed",
            message=str(e)
        )