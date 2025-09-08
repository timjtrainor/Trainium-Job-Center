"""API router configuration and endpoint registration."""
from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.jobspy import router as jobspy_router
from app.api.v1.endpoints.scheduler import router as scheduler_router
from app.api.v1.endpoints.crewai_review import router as crewai_review_router
from app.api.v1.endpoints.crewai_personal_brand import router as crewai_personal_brand_router
from app.api.v1.endpoints.chroma import router as chroma_router
from app.routes.jobs_fit_review import router as jobs_fit_review_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(jobspy_router, prefix="/jobs", tags=["jobs", "scraping"])
api_router.include_router(scheduler_router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(crewai_review_router, tags=["job-review", "crewai"])
api_router.include_router(crewai_personal_brand_router, tags=["job-review", "crewai"])
api_router.include_router(chroma_router, tags=["chroma", "vector-database"])
api_router.include_router(jobs_fit_review_router, tags=["job-posting-fit-review"])

__all__ = ["api_router"]
