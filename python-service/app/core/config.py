"""
Core application configuration and settings.
"""
from typing import Optional
import os
from loguru import logger
"""
Core application configuration and settings.
"""
from typing import Optional
import os
from loguru import logger


class Settings:
    """Application settings and configuration."""
    
    def __init__(self):
        # API Configuration
        self.app_name: str = "Trainium Python AI Service"
        self.app_version: str = "1.0.0"
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        
        # Server Configuration
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        
        # Logging Configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
        
        # Gemini AI Configuration (for future use)
        self.gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        
        # PostgREST Configuration (for future integration)
        self.postgrest_url: str = os.getenv("POSTGREST_URL", "http://postgrest:3000")
        
        # Environment-based configuration
        self.environment: str = os.getenv("ENVIRONMENT", "development")


# Global settings instance
settings = Settings()


def configure_logging():
    """Configure structured logging for the application."""
    
    # Remove default logger
    logger.remove()
    
    # Add structured logging
    logger.add(
        sink=lambda message: print(message, end=''),
        format=settings.log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file logging for production
    if settings.environment == "production":
        logger.add(
            "logs/app.log",
            rotation="1 day",
            retention="30 days",
            format=settings.log_format,
            level=settings.log_level
        )
    
    logger.info(f"Logging configured with level: {settings.log_level}")


def get_settings() -> Settings:
    """Get application settings."""
    return settings