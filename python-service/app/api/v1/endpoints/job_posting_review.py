"""
API endpoints for job posting review CrewAI functionality.
"""
from typing import Dict, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from pydantic import BaseModel, Field

from ....schemas.responses import StandardResponse, create_success_response, create_error_response
from ....services.crewai.job_posting_review.crew import get_job_posting_review_crew, run_crew

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
    Analyze a job posting using the CrewAI job posting review system.
    
    This endpoint runs the orchestrated crew that performs:
    1. **Job intake and parsing** - Extract structured data from raw job posting
    2. **Pre-filtering** - Apply hard rejection rules (salary, seniority, location)
    3. **Quick fit analysis** - Score career growth, compensation, lifestyle, purpose alignment  
    4. **Brand framework matching** - Compare against career brand framework in ChromaDB
    5. **Final orchestration** - Managing agent provides final recommendation
    
    The crew uses a hierarchical process where the managing agent controls the workflow
    and only proceeds to deeper analysis if the job passes initial filters.
    
    Args:
        job_input: JobPostingInput containing job posting data and optional configuration
    
    Returns:
        Structured analysis results with recommendation, reasoning, and scores
    """
    try:
        # Convert job posting to dictionary format for processing
        if isinstance(job_input.job_posting, str):
            job_data = {"raw_text": job_input.job_posting}
        else:
            job_data = job_input.job_posting
            
        # Run the crew using the existing run_crew function for compatibility
        result = run_crew(
            job_posting_data=job_data,
            options=job_input.options or {},
            correlation_id=None  # Could generate UUID here if needed
        )
        
        return create_success_response(
            data=result,
            message="Job posting analysis completed successfully"
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
    Simplified endpoint for job posting analysis with just the job posting data.
    
    Args:
        job_posting: Job posting as string or dictionary
    
    Returns:
        Analysis results from the CrewAI crew
    """
    try:
        # Use the crew directly for simpler interface
        crew = get_job_posting_review_crew()
        
        # Convert job posting to string for the crew input
        job_posting_str = job_posting if isinstance(job_posting, str) else str(job_posting)
        
        # Run the crew with the job posting
        result = crew.kickoff(inputs={"job_posting": job_posting_str})
        
        return create_success_response(
            data={"result": str(result), "crew_output": True},
            message="Job posting analysis completed successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to analyze job posting: {str(e)}")
        return create_error_response(
            error="Job posting analysis failed",
            message=str(e)
        )


@router.get("/health", response_model=StandardResponse) 
async def health_check():
    """
    Health check for the job posting review CrewAI service.
    
    Returns:
        Service health status and crew configuration details
    """
    try:
        crew = get_job_posting_review_crew()
        
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
            "service": "JobPostingReviewCrew",
            "agents_count": len(crew.agents),
            "tasks_count": len(crew.tasks),
            "process": str(crew.process),
            "agents": agent_info,
            "tasks": task_info,
            "status": "healthy"
        }
        
        return create_success_response(
            data=health_status,
            message="Job posting review service is healthy"
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_error_response(
            error="Health check failed", 
            message=str(e)
        )


@router.get("/config", response_model=StandardResponse)
async def get_crew_config():
    """
    Get the configuration details of the job posting review crew.
    
    Returns:
        Crew configuration including agents, tasks, and process details
    """
    try:
        crew = get_job_posting_review_crew()
        
        config_info = {
            "crew_type": "JobPostingReviewCrew",
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
            1. Job Intake Agent: Parse job posting into structured JSON
            2. Pre-Filter Agent: Apply hard rejection rules (salary, seniority, location)  
            3. Quick Fit Analyst: Score career growth, compensation, lifestyle, purpose
            4. Brand Framework Matcher: Compare against career brand framework
            5. Managing Agent: Orchestrate workflow and provide final recommendation
            """
        }
        
        return create_success_response(
            data=config_info,
            message="Crew configuration retrieved successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to get crew config: {str(e)}")
        return create_error_response(
            error="Failed to retrieve crew configuration",
            message=str(e)
        )