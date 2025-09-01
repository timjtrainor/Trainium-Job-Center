"""
Trainium Python AI Service - FastAPI Application
Main entry point for the FastAPI-based microservice that provides AI capabilities
for the Trainium Job Center application.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import traceback

from app.core.config import configure_logging, get_settings
from app.api import api_router
from app.services.gemini import get_gemini_service
from app.services.postgrest import get_postgrest_service
from app.services.jobspy_ingestion import get_jobspy_service
from app.services.scheduler_service import get_scheduler_service
from app.models.responses import create_error_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    Handles startup and shutdown events.
    """
    # Configure logging first
    configure_logging()
    settings = get_settings()
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize services
    gemini_service = get_gemini_service()
    postgrest_service = get_postgrest_service()
    jobspy_service = get_jobspy_service()
    scheduler_service = get_scheduler_service()
    
    try:
        # Initialize Gemini service
        await gemini_service.initialize()
        
        # Initialize PostgREST service  
        await postgrest_service.initialize()
        
        # Initialize JobSpy service
        await jobspy_service.initialize()
        
        # Initialize Scheduler service
        await scheduler_service.initialize()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        # Continue anyway - services will handle their own initialization on first use
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down services...")
    await postgrest_service.close()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Trainium Python AI Service",
    description="""
    FastAPI-based microservice for the Trainium Job Center application.
    
    This service provides:
    - AI-powered job application assistance via Gemini AI
    - Job scraping and ingestion from major job boards (Indeed, LinkedIn, Glassdoor, etc.)
    - Integration with PostgREST backend for data access
    - Scheduler service for managing follow-ups, reminders, and due dates
    - Health monitoring and system status endpoints
    - Structured logging and error handling
    - Async processing capabilities for long-running AI tasks
    
    Built with modularity and extensibility in mind for future AI enhancements.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    response = create_error_response(
        error=f"HTTP {exc.status_code}",
        message=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured error responses."""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    response = create_error_response(
        error="Internal server error",
        message="An unexpected error occurred" if not settings.debug else str(exc)
    )
    
    return JSONResponse(
        status_code=500,
        content=response.dict()
    )


# Include API routers
app.include_router(api_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic service information."""
    settings = get_settings()
    
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "description": "FastAPI microservice for Trainium Job Center AI capabilities"
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )