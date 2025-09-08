"""Core application configuration and settings."""

from typing import Optional, Union
import os
from urllib.parse import urlparse
from loguru import logger
from dotenv import load_dotenv
import chromadb


class Settings:
    """Application settings and configuration."""

    def __init__(self):
        load_dotenv()
        # API Configuration
        self.app_name: str = "Trainium Python AI Service"
        self.app_version: str = "1.0.0"
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"

        # Server Configuration
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))

        # Logging Configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_format: str = (
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
        )

        # AI Provider API Keys
        self.gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.ollama_api_key: Optional[str] = os.getenv("OLLAMA_API_KEY")  # Optional for local
        self.anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.tavily_api_key: Optional[str] = os.getenv("TAVILY_API_KEY")  # For web search
        
        # LLM Configuration
        self.llm_preference: str = os.getenv(
            "LLM_PREFERENCE", 
            "ollama:gemma3:1b,gemini:gemini-1.5-flash,openai:gpt-4o-mini"
        )
        self.ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        # ChromaDB Configuration
        self.chroma_url: str = os.getenv("CHROMA_URL", "chromadb")
        self.chroma_port: int = int(os.getenv("CHROMA_PORT", "8000"))
        
        # Embedding Configuration
        self.embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "sentence_transformer")
        self.embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

        # PostgREST Configuration (for future integration)
        self.postgrest_url: str = os.getenv("POSTGREST_URL", "http://postgrest:3000")

        # Database Configuration for direct access
        self.database_url: str = os.getenv("DATABASE_URL", "")
        if not self.database_url:
            raise ValueError("DATABASE_URL is not set")

        parsed_db = urlparse(self.database_url)
        if parsed_db.hostname in {"localhost", "127.0.0.1"} or (
            parsed_db.port and parsed_db.port != 5432
        ):
            logger.warning(
                "DATABASE_URL may be misconfigured for Docker: %s", self.database_url
            )

        # Redis Configuration for queue system
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_host: str = os.getenv("REDIS_HOST", "localhost")
        self.redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db: int = int(os.getenv("REDIS_DB", "0"))

        # Queue Configuration
        self.rq_queue_name: str = os.getenv("RQ_QUEUE_NAME", "scraping")
        self.rq_result_ttl: int = int(os.getenv("RQ_RESULT_TTL", "3600"))  # 1 hour
        self.rq_job_timeout: int = int(os.getenv("RQ_JOB_TIMEOUT", "900"))  # 15 minutes

        # Environment-based configuration
        self.environment: str = os.getenv("ENVIRONMENT", "development")

    def create_chroma_client(self) -> Union[chromadb.HttpClient, chromadb.PersistentClient]:
        """Create and return a ChromaDB client using configured settings.

        Falls back to a persistent client if the HTTP client is unavailable.
        """
        try:
            client = chromadb.HttpClient(host=self.chroma_url, port=self.chroma_port)
            client.heartbeat()
            logger.info(
                f"Connected to ChromaDB HTTP server at {self.chroma_url}:{self.chroma_port}"
            )
            return client
        except Exception as e:  # pragma: no cover - network issues
            logger.warning(f"Could not connect to ChromaDB HTTP server: {e}")
            try:
                persist_path = "./data/chroma"
                os.makedirs(persist_path, exist_ok=True)
                client = chromadb.PersistentClient(path=persist_path)
                logger.info(f"Using ChromaDB persistent client at {persist_path}")
                return client
            except Exception as e:  # pragma: no cover - unlikely error
                logger.error(f"Failed to initialize ChromaDB persistent client: {e}")
                raise RuntimeError(f"Could not initialize any ChromaDB client: {e}")


# Global settings instance
settings = Settings()


def configure_logging():
    """Configure structured logging for the application."""

    # Remove default logger
    logger.remove()

    # Add structured logging
    logger.add(
        sink=lambda message: print(message, end=""),
        format=settings.log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file logging for production
    if settings.environment == "production":
        logger.add(
            "logs/app.log",
            rotation="1 day",
            retention="30 days",
            format=settings.log_format,
            level=settings.log_level,
        )

    logger.info(f"Logging configured with level: {settings.log_level}")


def resolve_api_key(provider: str) -> Optional[str]:
    """Return the API key for a given provider name."""
    provider = provider.lower()
    mapping = {
        "openai": settings.openai_api_key,
        "ollama": settings.ollama_api_key,  # Optional for local usage
        "gemini": settings.gemini_api_key,
        "anthropic": settings.anthropic_api_key,
        "tavily": settings.tavily_api_key,
    }
    return mapping.get(provider)


def get_settings() -> Settings:
    """Get application settings."""
    return settings
