"""
API router configuration and endpoint registration.
"""
from fastapi import APIRouter
from .health import router as health_router
from .jobspy import router as jobspy_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, tags=["health"])
api_router.include_router(jobspy_router, prefix="/jobs", tags=["jobs", "scraping"])

# Future: Add other routers here
# api_router.include_router(gemini_router, prefix="/ai", tags=["ai"])