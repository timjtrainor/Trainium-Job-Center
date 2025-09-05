"""
API endpoints for CrewAI job review functionality.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import yaml
from fastapi import APIRouter, HTTPException, Query, Depends
from loguru import logger

from ....schemas.responses import (
    StandardResponse,
    create_success_response,
    create_error_response,
)
from ....dependencies import get_job_review_crew, get_database_service
from ....services.crewai import JobReviewCrew
from ....services.infrastructure.database import DatabaseService

router = APIRouter(prefix="/jobs", tags=["Job Review"])


@router.post("/review", response_model=StandardResponse)
async def review_single_job(
    job_data: Dict[str, Any],
    job_review_crew: JobReviewCrew = Depends(get_job_review_crew),
):
    """
    Analyze a single job using CrewAI multi-agent review system.
    
    Args:
        job_data: Dictionary containing job information (title, company, description, etc.)
    
    Returns:
        Comprehensive job analysis with recommendations
    """
    try:
        crew = job_review_crew.job_review()
        analysis = crew.kickoff(inputs={"job": job_data})

        return create_success_response(
            data=analysis,
            message="Job analysis completed successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to review job: {str(e)}")
        return create_error_response(
            error="Failed to analyze job",
            message=str(e)
        )


@router.post("/review/batch", response_model=StandardResponse)
async def review_multiple_jobs(
    jobs_data: List[Dict[str, Any]],
    job_review_crew: JobReviewCrew = Depends(get_job_review_crew),
):
    """
    Analyze multiple jobs using CrewAI multi-agent review system.
    
    Args:
        jobs_data: List of dictionaries containing job information
    
    Returns:
        List of job analyses sorted by recommendation quality
    """
    try:
        if len(jobs_data) > 50:
            raise HTTPException(
                status_code=400, 
                detail="Cannot analyze more than 50 jobs at once"
            )
        
        review_crew = job_review_crew

        analyses = []
        for job in jobs_data:
            result = review_crew.job_review().kickoff(inputs={"job": job})
            analyses.append(result)

        return create_success_response(
            data={"analyses": analyses, "total_analyzed": len(analyses)},
            message=f"Successfully analyzed {len(analyses)} jobs"
        )
    
    except Exception as e:
        logger.error(f"Failed to review jobs batch: {str(e)}")
        return create_error_response(
            error="Failed to analyze jobs batch",
            message=str(e)
        )


@router.get("/review/from-db", response_model=StandardResponse)
async def review_jobs_from_database(
    limit: int = Query(10, ge=1, le=50, description="Number of jobs to analyze"),
    site: Optional[str] = Query(None, description="Filter by job site"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    title_contains: Optional[str] = Query(None, description="Filter jobs with title containing this text"),
    job_review_crew: JobReviewCrew = Depends(get_job_review_crew),
    db_service: DatabaseService = Depends(get_database_service),
):
    """
    Analyze jobs from the database using CrewAI multi-agent review system.
    
    Args:
        limit: Number of jobs to analyze (max 50)
        site: Optional filter by job site
        company: Optional filter by company name
        title_contains: Optional filter by job title content
    
    Returns:
        Job analyses with database job IDs
    """
    try:
        review_crew = job_review_crew

        if not db_service.initialized:
            await db_service.initialize()
        if not db_service.pool:
            raise RuntimeError("Database connection pool is not initialized")
        
        # Build SQL query with filters
        query = """
            SELECT id, site, title, company, description, location_state, location_city, 
                   is_remote, min_amount as salary_min, max_amount as salary_max,
                   interval, ingested_at, job_url
            FROM jobs 
            WHERE 1=1
        """
        params = []
        
        if site:
            query += " AND LOWER(site) = LOWER($%d)" % (len(params) + 1)
            params.append(site)
        
        if company:
            query += " AND LOWER(company) ILIKE LOWER($%d)" % (len(params) + 1)
            params.append(f"%{company}%")
        
        if title_contains:
            query += " AND LOWER(title) ILIKE LOWER($%d)" % (len(params) + 1)
            params.append(f"%{title_contains}%")
        
        query += " ORDER BY ingested_at DESC LIMIT $%d" % (len(params) + 1)
        params.append(limit)
        
        # Fetch jobs from database
        async with db_service.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        
        if not rows:
            return create_success_response(
                data={"analyses": [], "total_analyzed": 0},
                message="No jobs found matching the criteria"
            )
        
        # Convert database rows to job data format
        jobs_data = []
        for row in rows:
            job_data = {
                "title": row["title"],
                "company": row["company"],
                "description": row["description"],
                "location_state": row["location_state"],
                "location_city": row["location_city"],
                "is_remote": row["is_remote"],
                "salary_min": row["salary_min"],
                "salary_max": row["salary_max"],
                "interval": row["interval"],
                "site": row["site"],
                "job_url": row["job_url"]
            }
            job_data = {k: (float(v) if isinstance(v, Decimal) else v) for k, v in job_data.items()}
            jobs_data.append(job_data)

        analyses = [review_crew.job_review().kickoff(inputs={"job": job}) for job in jobs_data]

        return create_success_response(
            data={
                "analyses": analyses,
                "total_analyzed": len(analyses),
                "filters_applied": {
                    "site": site,
                    "company": company,
                    "title_contains": title_contains,
                    "limit": limit
                }
            },
            message=f"Successfully analyzed {len(analyses)} jobs from database"
        )
    
    except Exception as e:
        logger.error(f"Failed to review jobs from database: {str(e)}")
        return create_error_response(
            error="Failed to analyze jobs from database",
            message=str(e)
        )


@router.get("/review/agents", response_model=StandardResponse)
async def get_available_agents():
    """Get information about available analysis agents."""
    try:
        base_dir = Path(__file__).resolve().parent.parent / "services" / "crewai" / "agents"
        agents = []
        for path in base_dir.glob("*.yaml"):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            agents.append({
                "name": data.get("id"),
                "persona_type": data.get("persona_type"),
                "description": data.get("role"),
                "decision_lens": data.get("metadata", {}).get("decision_lens"),
                "capabilities": data.get("metadata", {}).get("capabilities", []),
            })
        agents_info = {
            "agents": agents,
            "analysis_outputs": [
                "required_skills",
                "preferred_skills",
                "experience_level",
                "education_requirements",
                "salary_analysis",
                "benefits_mentioned",
                "job_quality_score",
                "description_completeness",
                "red_flags",
                "green_flags",
                "company_insights",
                "overall_recommendation",
                "confidence_score",
            ],
        }
        return create_success_response(
            data=agents_info,
            message="Available agents information retrieved successfully",
        )
    except Exception as e:
        logger.error(f"Failed to get agents info: {str(e)}")
        return create_error_response(
            error="Failed to retrieve agents information",
            message=str(e)
        )

@router.get("/review/health", response_model=StandardResponse)
async def health_check():
    """
    Health check for the CrewAI job review service.
    
    Returns:
        Service health status and initialization state
    """
    try:
        crew = get_job_review_crew()

        health_status = {
            "service": "JobReviewCrew",
            "agents_available": list(crew.agents.keys()),
            "timestamp": str(datetime.now())
        }

        return create_success_response(
            data=health_status,
            message="Service health check completed"
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_error_response(
            error="Health check failed",
            message=str(e)
        )

