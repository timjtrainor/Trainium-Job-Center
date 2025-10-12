"""API router configuration and endpoint registration."""
from fastapi import APIRouter

from .v1.endpoints.health import router as health_router
from .v1.endpoints.jobspy import router as jobspy_router
from .v1.endpoints.scheduler import router as scheduler_router
from .v1.endpoints.crewai_personal_brand import router as crewai_personal_brand_router
from .v1.endpoints.job_posting_review import router as job_posting_review_router
from .v1.endpoints.job_review import router as job_review_router
from .v1.endpoints.jobs import router as jobs_router
from .v1.endpoints.chroma import router as chroma_router
from .v1.endpoints.chroma_manager import router as chroma_manager_router
from .v1.endpoints.career_brand import router as career_brand_router
from .v1.endpoints.company import router as company_router
from .v1.endpoints.linkedin_job_search import router as linkedin_job_search_router
from .v1.endpoints.linkedin_recommended_jobs import router as linkedin_recommended_jobs_router
from .v1.endpoints.brand_driven_job_search import router as brand_driven_job_search_router
from .v1.endpoints.linkedin_jobs import router as linkedin_jobs_router
from .v1.endpoints.applications import router as applications_router
from .v1.endpoints.glassdoor_enrichment import router as glassdoor_enrichment_router
from .v1.endpoints.resume_documents import router as resume_documents_router

from ..routes.jobs_fit_review import router as jobs_fit_review_router

api_router = APIRouter(prefix="/api")

api_router.include_router(jobspy_router, prefix="/job-feed", tags=["Job Feed"])
api_router.include_router(scheduler_router, prefix="/scheduler", tags=["Scheduler"])
api_router.include_router(crewai_personal_brand_router, prefix="/crewai", tags=["CrewAI"])
api_router.include_router(job_posting_review_router, prefix="/crewai", tags=["CrewAI"])
api_router.include_router(chroma_router, tags=["Vector-Database"])
api_router.include_router(chroma_manager_router, tags=["ChromaDB Manager"])
api_router.include_router(career_brand_router, tags=["Career Brand"])

api_router.include_router(company_router, prefix="/company-research")
api_router.include_router(linkedin_job_search_router, prefix="/crewai", tags=["CrewAI"])
api_router.include_router(linkedin_recommended_jobs_router, prefix="/crewai", tags=["CrewAI"])
api_router.include_router(brand_driven_job_search_router, prefix="/crewai", tags=["CrewAI"])

# Job Review Management
api_router.include_router(job_review_router, tags=["Job Review"])

# Jobs API
api_router.include_router(jobs_router, tags=["Jobs"])
api_router.include_router(linkedin_jobs_router, tags=["LinkedIn Jobs"])
api_router.include_router(applications_router, tags=["Applications"])
api_router.include_router(glassdoor_enrichment_router, tags=["Glassdoor Enrichment"])
api_router.include_router(resume_documents_router, tags=["Resumes"])

# Health check
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(jobs_fit_review_router, tags=["job-posting-fit-review"])

__all__ = ["api_router"]
