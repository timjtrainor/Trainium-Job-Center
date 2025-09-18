"""
API endpoints for Brand-Driven Job Search CrewAI functionality.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from ....schemas.responses import StandardResponse, create_success_response, create_error_response
from ....schemas.brand_driven_job_search import (
    BrandDrivenJobSearchRequest, 
    BrandDrivenJobSearchResponse,
    BrandSearchStatus
)
from ....services.crewai.brand_driven_job_search.crew import get_brand_driven_job_search_crew
from ....services.crewai.brand_driven_job_search.brand_search import brand_search_helper

router = APIRouter(prefix="/brand-driven-job-search", tags=["Brand-Driven Job Search"])


@router.post("/search", response_model=StandardResponse)
async def execute_brand_driven_search(request: BrandDrivenJobSearchRequest):
    """
    Execute autonomous brand-driven LinkedIn job search.
    
    This endpoint uses CrewAI agents to:
    1. Extract career brand data from ChromaDB for the user
    2. Generate targeted LinkedIn search queries from brand dimensions  
    3. Execute LinkedIn searches using derived queries
    4. Score job results for brand alignment across all dimensions
    5. Return prioritized, brand-aligned job opportunities
    
    Args:
        request: Brand-driven job search parameters
    
    Returns:
        Brand-aligned job search results with scoring and insights
    """
    try:
        logger.info(f"Starting brand-driven job search for user: {request.user_id}")
        
        # Get the crew and execute search
        crew = get_brand_driven_job_search_crew()
        result = await crew.execute_brand_driven_search(request.user_id)
        
        # Check if search was successful
        if not result.get("success", False):
            return create_error_response(
                error="Brand-driven job search failed",
                message=result.get("error", "Unknown error occurred")
            )
        
        # Transform result to response schema
        response_data = BrandDrivenJobSearchResponse(
            success=result.get("success", True),
            brand_driven_jobs=result.get("brand_driven_jobs", []),
            execution_summary=result.get("execution_summary", {}),
            brand_insights=result.get("brand_insights"),
            user_id=request.user_id,
        )
        
        return create_success_response(
            data=response_data.model_dump(),
            message=f"Brand-driven search completed: {len(response_data.brand_driven_jobs)} aligned jobs found"
        )
        
    except Exception as e:
        logger.error(f"Brand-driven job search API error: {str(e)}")
        return create_error_response(
            error="Brand-driven job search failed",
            message=str(e)
        )


@router.get("/status/{user_id}", response_model=StandardResponse)
async def get_brand_search_status(user_id: str):
    """
    Check brand data availability for autonomous job search.
    
    This endpoint checks whether sufficient career brand data exists in ChromaDB
    for the specified user to execute a meaningful brand-driven job search.
    
    Args:
        user_id: User ID to check brand data availability for
    
    Returns:
        Status of brand data availability and search feasibility
    """
    try:
        logger.info(f"Checking brand search status for user: {user_id}")
        
        crew = get_brand_driven_job_search_crew()
        status = crew.get_brand_search_status(user_id)
        
        response_data = BrandSearchStatus(
            user_id=user_id,
            brand_data_available=status.get("brand_data_available", False),
            brand_sections=status.get("brand_sections", []),
            can_execute_search=status.get("can_execute_search", False),
            error=status.get("error")
        )
        
        return create_success_response(
            data=response_data.model_dump(),
            message=f"Brand search status retrieved for user {user_id}"
        )
        
    except Exception as e:
        logger.error(f"Brand search status check failed: {str(e)}")
        return create_error_response(
            error="Status check failed",
            message=str(e)
        )


@router.get("/brand-queries/{user_id}", response_model=StandardResponse)
async def generate_brand_queries(user_id: str):
    """
    Generate LinkedIn search queries from user's career brand data.
    
    This endpoint demonstrates the first step of brand-driven search by
    extracting career brand dimensions and generating targeted search queries
    without executing the actual LinkedIn searches.
    
    Args:
        user_id: User ID for brand data retrieval
    
    Returns:
        Generated search queries organized by brand section
    """
    try:
        logger.info(f"Generating brand queries for user: {user_id}")
        
        # Generate search queries using the brand search helper
        search_queries = await brand_search_helper.generate_search_queries(user_id)
        
        if not search_queries:
            return create_error_response(
                error="No brand data found",
                message=f"No career brand data available for user {user_id}"
            )
        
        response_data = {
            "success": True,
            "brand_queries": search_queries,
            "total_queries": len(search_queries),
            "user_id": user_id
        }
        
        return create_success_response(
            data=response_data,
            message=f"Generated {len(search_queries)} brand-driven search queries"
        )
        
    except Exception as e:
        logger.error(f"Brand query generation failed: {str(e)}")
        return create_error_response(
            error="Brand query generation failed",
            message=str(e)
        )


@router.get("/health", response_model=StandardResponse)
async def health_check():
    """Health check for brand-driven job search crew."""
    try:
        crew = get_brand_driven_job_search_crew()
        
        # Basic health check
        health_data = {
            "crew_initialized": crew is not None,
            "linkedin_tools_loaded": len(crew._linkedin_tools) > 0 if hasattr(crew, '_linkedin_tools') else False,
            "chroma_tools_loaded": len(crew._chroma_tools) > 0 if hasattr(crew, '_chroma_tools') else False,
            "agents_count": len(crew.crew().agents) if crew else 0,
            "tasks_count": len(crew.crew().tasks) if crew else 0,
            "brand_sections": brand_search_helper.BRAND_SECTIONS
        }
        
        return create_success_response(
            data=health_data,
            message="Brand-driven job search crew is healthy"
        )
        
    except Exception as e:
        logger.error(f"Brand-driven job search health check failed: {str(e)}")
        return create_error_response(
            error="Health check failed",
            message=str(e)
        )


@router.get("/config", response_model=StandardResponse)
async def get_crew_config():
    """Get brand-driven job search crew configuration details."""
    try:
        crew = get_brand_driven_job_search_crew()
        
        config_data = {
            "crew_type": "brand_driven_job_search",
            "process": "sequential",
            "agents": [
                {"name": "brand_query_generator", "role": "Career Brand Query Generator"},
                {"name": "linkedin_search_executor", "role": "LinkedIn Search Execution Specialist"},
                {"name": "brand_alignment_scorer", "role": "Brand-Job Alignment Specialist"},
                {"name": "orchestration_manager", "role": "Brand-Driven Job Search Coordinator"}
            ],
            "tasks": [
                {"name": "generate_brand_queries_task", "async": True},
                {"name": "execute_brand_searches_task", "async": True},
                {"name": "score_brand_alignment_task", "async": True},
                {"name": "compile_brand_driven_results_task", "async": False}
            ],
            "brand_sections": brand_search_helper.BRAND_SECTIONS,
            "linkedin_tools_available": len(crew._linkedin_tools) if hasattr(crew, '_linkedin_tools') else 0,
            "chroma_tools_available": len(crew._chroma_tools) if hasattr(crew, '_chroma_tools') else 0
        }
        
        return create_success_response(
            data=config_data,
            message="Brand-driven job search crew configuration retrieved"
        )
        
    except Exception as e:
        logger.error(f"Failed to get crew config: {str(e)}")
        return create_error_response(
            error="Configuration retrieval failed",
            message=str(e)
        )