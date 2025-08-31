"""
API router configuration and endpoint registration.
"""
from fastapi import APIRouter
from .health import router as health_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, tags=["health"])

# Future: Add other routers here
# api_router.include_router(gemini_router, prefix="/ai", tags=["ai"])
# api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])