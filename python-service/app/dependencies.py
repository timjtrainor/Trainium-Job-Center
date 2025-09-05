from fastapi import Request

from app.services.ai.gemini import GeminiService
from app.services.infrastructure.postgrest import PostgRESTService
from app.services.jobspy.ingestion import JobSpyIngestionService
from app.services.infrastructure.database import DatabaseService
from app.services.infrastructure.queue import QueueService
from app.services.infrastructure.scheduler import SchedulerService
from app.services.crewai import JobReviewCrew


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


def get_job_review_crew(request: Request) -> JobReviewCrew:
    """Retrieve the JobReviewCrew instance from application state."""
    return request.app.state.job_review_crew

