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
import json

from app.core.config import configure_logging, get_settings
from app.api.router import api_router
from app.services.ai.gemini import GeminiService
from app.services.infrastructure.postgrest import PostgRESTService
from app.services.jobspy.ingestion import JobSpyIngestionService
from app.services.infrastructure.database import DatabaseService
from app.services.infrastructure.queue import QueueService
from app.services.infrastructure.scheduler import SchedulerService
from app.services.crewai.research_company.crew import ResearchCompanyCrew
from app.schemas.responses import create_error_response
from app.services.startup import startup_tasks


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
    
    # Initialize services and store on application state
    app.state.gemini_service = GeminiService()
    app.state.postgrest_service = PostgRESTService()
    app.state.jobspy_service = JobSpyIngestionService()
    app.state.database_service = DatabaseService()
    app.state.queue_service = QueueService()
    app.state.scheduler_service = SchedulerService()
    app.state.company_crew = ResearchCompanyCrew()
    
    try:
        # Initialize existing services
        await app.state.gemini_service.initialize()
        await app.state.postgrest_service.initialize()
        await app.state.jobspy_service.initialize()

        # Initialize new queue-based services
        await app.state.database_service.initialize()
        await app.state.queue_service.initialize()
        await app.state.scheduler_service.initialize()
        
        # Initialize ChromaDB collections
        await startup_tasks()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        # Continue anyway - services will handle their own initialization on first use
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down services...")
    await app.state.postgrest_service.close()
    await app.state.database_service.close()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Trainium Python AI Service",
    description="""
    FastAPI-based microservice for the Trainium Job Center application.
    
    This service provides:
    - AI-powered job application assistance via Gemini AI
    - Job scraping and ingestion from major job boards (Indeed, LinkedIn, Glassdoor, etc.)
    - Queue-based scheduled job scraping with Redis and RQ
    - Integration with PostgREST backend for data access
    - Health monitoring and system status endpoints
    - Structured logging and error handling
    - Async processing capabilities for long-running AI and scraping tasks
    
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
    message = exc.detail
    if not isinstance(message, str):
        try:
            message = json.dumps(message)
        except TypeError:
            message = str(message)

    response = create_error_response(
        error=f"HTTP {exc.status_code}",
        message=message
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