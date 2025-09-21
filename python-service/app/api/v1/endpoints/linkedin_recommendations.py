"""API endpoints for LinkedIn Recommendations CrewAI functionality."""

from fastapi import APIRouter
from loguru import logger

from ....schemas.responses import StandardResponse, create_success_response, create_error_response
from ....services.crewai.linkedin_recommendations.crew import (
    get_linkedin_recommendations_crew,
    run_linkedin_recommendations,
)
from ....services.crewai.base import test_linkedin_mcp_connection_sync

router = APIRouter(prefix="/linkedin-recommendations", tags=["LinkedIn Recommendations"])


@router.post("/fetch", response_model=StandardResponse)
async def fetch_linkedin_recommendations():
    """
    Fetch personalized job recommendations from LinkedIn.
    
    This endpoint uses a single CrewAI agent to:
    1. Call LinkedIn's get_recommended_jobs MCP tool
    2. Retrieve personalized job recommendations based on user profile
    3. Return structured job data ready for database persistence
    
    Returns:
        JSON array of job objects with database-ready fields
    """
    try:
        logger.info("Starting LinkedIn recommendations fetch")
        
        result = run_linkedin_recommendations()

        success_flag = bool(result.get("success"))
        recommended_jobs = result.get("recommended_jobs") or []
        total_recommendations = result.get("total_recommendations")
        if total_recommendations is None:
            total_recommendations = len(recommended_jobs)

        if not success_flag or result.get("error"):
            error_message = result.get("error") or "LinkedIn recommendations fetch failed"
            return create_error_response(
                error="LinkedIn recommendations fetch failed",
                message=error_message,
                data=result,
            )

        if not recommended_jobs:
            return create_error_response(
                error="LinkedIn recommendations unavailable",
                message="No LinkedIn recommendations were returned.",
                data=result,
            )

        response_data = {
            **result,
            "recommended_jobs": recommended_jobs,
            "total_recommendations": total_recommendations,
        }

        return create_success_response(
            data=response_data,
            message=f"LinkedIn recommendations fetched: {total_recommendations} jobs found",
        )
        
    except Exception as e:
        logger.error(f"LinkedIn recommendations API error: {str(e)}")
        return create_error_response(
            error="LinkedIn recommendations fetch failed",
            message=str(e)
        )


@router.get("/health", response_model=StandardResponse)
async def health_check():
    """Health check for LinkedIn recommendations crew with MCP tool verification."""
    try:
        # Test LinkedIn MCP connection
        connection_status = test_linkedin_mcp_connection_sync()
        
        crew = get_linkedin_recommendations_crew()
        
        # Enhanced health check with MCP tool verification
        health_data = {
            "crew_initialized": crew is not None,
            "agents_count": len(crew.agents) if crew else 0,
            "tasks_count": len(crew.tasks) if crew else 0,
            "mcp_connection": {
                "status": "connected" if connection_status.get("success") else "failed",
                "total_tools": connection_status.get("total_tools", 0),
                "linkedin_tools_found": connection_status.get("linkedin_tools", []),
                "expected_tools_found": connection_status.get("expected_tools_found", []),
                "missing_tools": connection_status.get("missing_tools", []),
                "gateway_url": connection_status.get("gateway_url", "unknown")
            }
        }
        
        # Determine overall health
        is_healthy = (
            health_data["crew_initialized"] and 
            connection_status.get("success") and 
            len(connection_status.get("linkedin_tools", [])) > 0
        )
        
        message = "LinkedIn recommendations crew is healthy with MCP tools" if is_healthy else "LinkedIn recommendations crew has issues"
        
        if not is_healthy and connection_status.get("error"):
            return create_error_response(
                error="Health check failed",
                message=f"MCP connection issue: {connection_status.get('error')}"
            )
        
        return create_success_response(
            data=health_data,
            message=message
        )
        
    except Exception as e:
        logger.error(f"LinkedIn recommendations health check failed: {str(e)}")
        return create_error_response(
            error="Health check failed",
            message=str(e)
        )


@router.get("/config", response_model=StandardResponse)
async def get_crew_config():
    """Get LinkedIn recommendations crew configuration details."""
    try:
        crew = get_linkedin_recommendations_crew()
        
        config_data = {
            "crew_type": "linkedin_recommendations",
            "process": "sequential", 
            "agents": [
                {"name": "linkedin_recommendations_fetcher", "role": "LinkedIn Recommendations Specialist"}
            ],
            "tasks": [
                {"name": "fetch_recommended_jobs", "async": False}
            ],
            "linkedin_tools_available": len(crew._linkedin_tools) if hasattr(crew, '_linkedin_tools') else 0
        }
        
        return create_success_response(
            data=config_data,
            message="LinkedIn recommendations crew configuration retrieved"
        )
        
    except Exception as e:
        logger.error(f"Failed to get crew config: {str(e)}")
        return create_error_response(
            error="Configuration retrieval failed",
            message=str(e)
        )