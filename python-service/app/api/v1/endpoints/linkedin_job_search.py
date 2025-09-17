"""
API endpoints for LinkedIn job search functionality.
"""
import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from ....schemas.responses import StandardResponse, create_success_response, create_error_response
from ....schemas.linkedin_job_search import LinkedinJobSearchRequest, LinkedinJobSearchResponse
from ....services.crewai.linkedin_job_search import run_linkedin_job_search
from ....services.infrastructure.job_persistence import persist_jobs


router = APIRouter(prefix="/linkedin", tags=["LinkedIn Job Search"])


@router.post("/job-search", response_model=StandardResponse)
async def search_linkedin_jobs(search_request: LinkedinJobSearchRequest):
    """
    Search for jobs on LinkedIn using CrewAI agents with LinkedIn search tools.
    
    This endpoint executes a LinkedIn job search using the specified criteria and
    processes the results for database persistence. The workflow includes:
    
    1. **LinkedIn Search Agent** - Searches LinkedIn using provided criteria
    2. **Job Processing Agent** - Structures and validates search results  
    3. **Database Persistence** - Stores job results in the jobs table
    
    Args:
        search_request: LinkedIn job search parameters including job title, location, etc.
    
    Returns:
        Structured search results with metadata and persistence summary
    """
    try:
        # Convert request to dictionary for crew input
        search_params = search_request.model_dump(exclude_none=True)
        logger.info(f"Starting LinkedIn job search with params: {search_params}")
        
        # Execute the LinkedIn job search crew
        crew_result = run_linkedin_job_search(search_params)
        logger.info("LinkedIn job search crew execution completed")
        
        # Parse the crew result
        if isinstance(crew_result, str):
            try:
                crew_data = json.loads(crew_result)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse crew result as JSON: {e}")
                raise ValueError(f"Invalid crew response format: {e}")
        else:
            crew_data = crew_result
        
        # Extract processed jobs for database persistence
        processed_jobs = crew_data.get("processed_jobs", [])
        if not processed_jobs:
            logger.warning("No processed jobs found in crew result")
            return create_success_response(
                data={
                    "search_results": [],
                    "search_metadata": crew_data.get("search_metadata", {}),
                    "processing_summary": crew_data.get("processing_summary", {}),
                    "persistence_summary": {"inserted": 0, "skipped_duplicates": 0, "errors": []}
                },
                message="No jobs found matching search criteria"
            )
        
        # Persist jobs to database
        logger.info(f"Persisting {len(processed_jobs)} jobs to database")
        persistence_result = await persist_jobs(processed_jobs, "linkedin")
        logger.info(f"Job persistence completed: {persistence_result}")
        
        # Build response data
        response_data = {
            "search_results": processed_jobs,
            "search_metadata": crew_data.get("search_metadata", {}),
            "processing_summary": crew_data.get("processing_summary", {}),
            "persistence_summary": persistence_result
        }
        
        return create_success_response(
            data=response_data,
            message=f"LinkedIn job search completed successfully. Found {len(processed_jobs)} jobs, "
                   f"inserted {persistence_result.get('inserted', 0)} new records."
        )
        
    except ValueError as e:
        logger.error(f"Validation error in LinkedIn job search: {str(e)}")
        return create_error_response(
            error="Invalid search parameters",
            message=str(e)
        )
    except Exception as e:
        logger.error(f"LinkedIn job search failed: {str(e)}")
        return create_error_response(
            error="LinkedIn job search failed",
            message=str(e)
        )


@router.get("/health", response_model=StandardResponse)
async def health_check():
    """
    Health check for the LinkedIn job search service.
    
    Returns:
        Service health status and crew configuration details
    """
    try:
        from ....services.crewai.linkedin_job_search import get_linkedin_job_search_crew
        
        crew = get_linkedin_job_search_crew()
        
        # Get agent and task details
        agent_info = []
        for agent in crew.agents:
            agent_info.append({
                "role": getattr(agent, 'role', 'Unknown'),
                "goal": getattr(agent, 'goal', 'Unknown'),
                "tools_count": len(getattr(agent, 'tools', []))
            })
        
        task_info = []
        for task in crew.tasks:
            task_info.append({
                "description": getattr(task, 'description', 'Unknown')[:100] + "...",
                "agent_role": getattr(task.agent, 'role', 'Unknown') if hasattr(task, 'agent') else 'Unknown'
            })
        
        health_status = {
            "service": "LinkedinJobSearchCrew",
            "agents_count": len(crew.agents),
            "tasks_count": len(crew.tasks),
            "process": str(crew.process),
            "agents": agent_info,
            "tasks": task_info,
            "status": "healthy"
        }
        
        return create_success_response(
            data=health_status,
            message="LinkedIn job search service is healthy"
        )
    
    except Exception as e:
        logger.error(f"LinkedIn job search health check failed: {str(e)}")
        return create_error_response(
            error="Health check failed", 
            message=str(e)
        )


@router.get("/config", response_model=StandardResponse)
async def get_crew_config():
    """
    Get the configuration details of the LinkedIn job search crew.
    
    Returns:
        Crew configuration including agents, tasks, and process details
    """
    try:
        from ....services.crewai.linkedin_job_search import get_linkedin_job_search_crew
        
        crew = get_linkedin_job_search_crew()
        
        config_info = {
            "crew_type": "LinkedinJobSearchCrew",
            "process_type": str(crew.process),
            "agent_roles": [getattr(agent, 'role', 'Unknown') for agent in crew.agents],
            "task_flow": [
                {
                    "task_id": i,
                    "description": getattr(task, 'description', 'Unknown')[:200] + "...",
                    "agent": getattr(task.agent, 'role', 'Unknown') if hasattr(task, 'agent') else 'Unknown'
                }
                for i, task in enumerate(crew.tasks)
            ],
            "workflow_description": """
            1. LinkedIn Job Searcher: Search LinkedIn for jobs matching criteria
            2. Job Processor: Structure and validate search results for database persistence
            """
        }
        
        return create_success_response(
            data=config_info,
            message="Crew configuration retrieved successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to get LinkedIn crew config: {str(e)}")
        return create_error_response(
            error="Failed to retrieve crew configuration",
            message=str(e)
        )