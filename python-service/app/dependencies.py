from fastapi import Request

from .services.ai.gemini import GeminiService
from .services.infrastructure.postgrest import PostgRESTService
from .services.jobspy.ingestion import JobSpyIngestionService
from .services.infrastructure.database import DatabaseService
from .services.infrastructure.queue import QueueService
from .services.infrastructure.scheduler import SchedulerService
from .services.crewai.job_posting_review.crew import get_job_posting_review_crew


def get_gemini_service(request: Request) -> GeminiService:
    """Retrieve the Gemini service instance from application state."""
    return request.app.state.gemini_service


def get_postgrest_service(request: Request) -> PostgRESTService:
    """Retrieve the PostgREST service instance from application state."""
    return request.app.state.postgrest_service


def get_jobspy_service(request: Request) -> JobSpyIngestionService:
    """Retrieve the JobSpy ingestion service instance from application state."""
    return request.app.state.jobspy_service


def get_database_service(request: Request) -> DatabaseService:
    """Retrieve the database service instance from application state."""
    return request.app.state.database_service


def get_queue_service(request: Request) -> QueueService:
    """Retrieve the queue service instance from application state."""
    return request.app.state.queue_service


def get_scheduler_service(request: Request) -> SchedulerService:
    """Retrieve the scheduler service instance from application state."""
    return request.app.state.scheduler_service

