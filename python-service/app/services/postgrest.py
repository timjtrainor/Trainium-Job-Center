"""
PostgREST API client service for database operations.
This module provides the foundation for integrating with the PostgREST backend.
"""
from typing import Optional, Dict, Any, List
import httpx
from loguru import logger

from ..core.config import get_settings
from ..models.responses import StandardResponse, create_success_response, create_error_response


class PostgRESTService:
    """
    Service class for handling PostgREST API integration.
    Provides methods for communicating with the PostgREST backend.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.postgrest_url
        self.client = None
    
    async def initialize(self) -> bool:
        """
        Initialize the PostgREST service client.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=30.0
            )
            logger.info(f"PostgREST service initialized with base URL: {self.base_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgREST service: {str(e)}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the PostgREST service.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        try:
            if not self.client:
                await self.initialize()
            
            # Try to make a simple request to check connectivity
            response = await self.client.get("/")
            
            return {
                "service": "postgrest",
                "url": self.base_url,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_code": response.status_code
            }
            
        except Exception as e:
            logger.error(f"PostgREST health check failed: {str(e)}")
            return {
                "service": "postgrest",
                "url": self.base_url,
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_job_applications(self, user_id: Optional[str] = None) -> StandardResponse:
        """
        Get job applications from the database.
        
        Args:
            user_id (str, optional): Filter by specific user ID
        
        Returns:
            StandardResponse: Job applications data
        """
        try:
            if not self.client:
                await self.initialize()
            
            endpoint = "/job_applications"
            params = {}
            
            if user_id:
                params["user_id"] = f"eq.{user_id}"
            
            response = await self.client.get(endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return create_success_response(
                    data=data,
                    message=f"Retrieved {len(data)} job applications"
                )
            else:
                return create_error_response(
                    error=f"Failed to fetch job applications: HTTP {response.status_code}",
                    message=response.text
                )
                
        except Exception as e:
            logger.error(f"Error fetching job applications: {str(e)}")
            return create_error_response(
                error="Database query failed",
                message=str(e)
            )
    
    async def close(self):
        """Close the HTTP client connection."""
        if self.client:
            await self.client.aclose()
            logger.info("PostgREST service client closed")


# Global service instance
postgrest_service = PostgRESTService()


def get_postgrest_service() -> PostgRESTService:
    """Get the global PostgREST service instance."""
    return postgrest_service