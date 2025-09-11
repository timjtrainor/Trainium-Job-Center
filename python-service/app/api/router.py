"""API router configuration and endpoint registration."""
from fastapi import APIRouter

from .v1.endpoints.health import router as health_router
from .v1.endpoints.jobspy import router as jobspy_router
from .v1.endpoints.scheduler import router as scheduler_router
from .v1.endpoints.crewai_review import router as crewai_review_router
from .v1.endpoints.crewai_personal_brand import router as crewai_personal_brand_router
from .v1.endpoints.chroma import router as chroma_router
from .v1.endpoints.company import router as company_router

from ..routes.jobs_fit_review import router as jobs_fit_review_router

api_router = APIRouter()

api_router.include_router(jobspy_router, prefix="/job-feed", tags=["Job Feed"])
api_router.include_router(scheduler_router, prefix="/scheduler", tags=["Scheduler"])
api_router.include_router(crewai_review_router, prefix="/crewai", tags=["CrewAI"])
api_router.include_router(crewai_personal_brand_router, prefix="/crewai", tags=["CrewAI"])
api_router.include_router(chroma_router, tags=["Vector-Database"])

api_router.include_router(company_router, prefix="/company-research")

# Health check
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(jobs_fit_review_router, tags=["job-posting-fit-review"])

__all__ = ["api_router"]
