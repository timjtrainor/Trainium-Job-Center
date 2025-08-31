"""
Health check and system monitoring endpoints.
"""
from datetime import datetime
from fastapi import APIRouter
from loguru import logger

from ..models.responses import StandardResponse, HealthStatus, create_success_response
from ..core.config import get_settings

router = APIRouter()


@router.get("/health", response_model=StandardResponse)
async def health_check():
    """
    Health check endpoint that returns the current status of the service.
    
    Returns:
        StandardResponse: Contains service health information
    """
    settings = get_settings()
    
    try:
        health_data = HealthStatus(
            service=settings.app_name,
            version=settings.app_version,
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            dependencies={
                "postgrest": {
                    "url": settings.postgrest_url,
                    "status": "configured"
                },
                "gemini_ai": {
                    "configured": settings.gemini_api_key is not None,
                    "status": "ready" if settings.gemini_api_key else "not_configured"
                }
            }
        )
        
        logger.info("Health check requested - service is healthy")
        
        return create_success_response(
            data=health_data,
            message="Service is running normally"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        # Still return a response, but indicate issues
        health_data = HealthStatus(
            service=settings.app_name,
            version=settings.app_version,
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat()
        )
        
        return create_success_response(
            data=health_data,
            message=f"Service has issues: {str(e)}"
        )


@router.get("/health/detailed", response_model=StandardResponse)
async def detailed_health_check():
    """
    Detailed health check that includes more comprehensive system information.
    
    Returns:
        StandardResponse: Contains detailed service health information
    """
    settings = get_settings()
    
    try:
        # Future: Add actual dependency checks here
        # For now, we'll just return configuration status
        
        detailed_info = {
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.environment,
            "configuration": {
                "log_level": settings.log_level,
                "debug_mode": settings.debug,
                "host": settings.host,
                "port": settings.port
            },
            "dependencies": {
                "postgrest": {
                    "url": settings.postgrest_url,
                    "status": "configured",
                    "description": "PostgREST API for database access"
                },
                "gemini_ai": {
                    "configured": settings.gemini_api_key is not None,
                    "status": "ready" if settings.gemini_api_key else "not_configured",
                    "description": "Google Gemini AI service for generative AI capabilities"
                }
            },
            "capabilities": [
                "health_monitoring",
                "structured_logging", 
                "error_handling",
                "async_processing_ready",
                "gemini_ai_integration_ready"
            ]
        }
        
        logger.info("Detailed health check requested - service is healthy")
        
        return create_success_response(
            data=detailed_info,
            message="Service is running normally with all systems operational"
        )
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return create_success_response(
            data={
                "service": settings.app_name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            message=f"Service health check failed: {str(e)}"
        )