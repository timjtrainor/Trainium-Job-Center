"""
Tests for job review service functionality.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.infrastructure.job_review_service import JobReviewService
from app.services.infrastructure.database import DatabaseService
from app.services.infrastructure.queue import QueueService


@pytest.fixture
def mock_db_service():
    """Mock database service."""
    service = Mock(spec=DatabaseService)
    service.initialized = True
    service.initialize = AsyncMock(return_value=True)
    return service


@pytest.fixture  
def mock_queue_service():
    """Mock queue service."""
    service = Mock(spec=QueueService)
    service.initialized = True
    service.initialize = AsyncMock(return_value=True)
    service.enqueue_multiple_job_reviews = Mock()
    return service


@pytest.fixture
def job_review_service(mock_db_service, mock_queue_service):
    """Job review service with mocked dependencies."""
    service = JobReviewService()
    service.db_service = mock_db_service
    service.queue_service = mock_queue_service
    service.initialized = True
    return service


@pytest.mark.asyncio
async def test_queue_pending_jobs_success(job_review_service, mock_db_service, mock_queue_service):
    """Test successful queuing of pending jobs."""
    # Setup mock data
    mock_jobs = [
        {"id": uuid4(), "title": "Python Developer", "company": "Tech Corp"},
        {"id": uuid4(), "title": "Data Scientist", "company": "Data Inc"}
    ]
    mock_db_service.get_pending_review_jobs.return_value = mock_jobs
    
    mock_results = {str(job["id"]): f"task_{i}" for i, job in enumerate(mock_jobs)}
    mock_queue_service.enqueue_multiple_job_reviews.return_value = mock_results
    
    # Test
    result = await job_review_service.queue_pending_jobs(limit=10, max_retries=3)
    
    # Assertions
    assert result["status"] == "success"
    assert result["queued_count"] == 2
    assert result["failed_count"] == 0
    assert "Queued 2/2 jobs" in result["message"]
    
    mock_db_service.get_pending_review_jobs.assert_called_once_with(10)
    mock_queue_service.enqueue_multiple_job_reviews.assert_called_once()


@pytest.mark.asyncio
async def test_queue_pending_jobs_no_jobs(job_review_service, mock_db_service):
    """Test queuing when no pending jobs exist."""
    mock_db_service.get_pending_review_jobs.return_value = []
    
    result = await job_review_service.queue_pending_jobs()
    
    assert result["status"] == "success"
    assert result["queued_count"] == 0
    assert "No pending jobs" in result["message"]


@pytest.mark.asyncio
async def test_get_review_status_job_exists(job_review_service, mock_db_service):
    """Test getting review status for existing job."""
    job_id = str(uuid4())
    mock_job = {
        "id": job_id,
        "title": "Senior Developer",
        "company": "TechCorp",
        "status": "reviewed"
    }
    from datetime import datetime
    mock_review = {
        "recommend": True,
        "confidence": "high",
        "rationale": "Great fit",
        "retry_count": 0,
        "error_message": None,
        "created_at": datetime(2024, 1, 1),
        "updated_at": datetime(2024, 1, 1, 1)
    }
    
    mock_db_service.get_job_by_id.return_value = mock_job
    mock_db_service.get_job_review.return_value = mock_review
    
    result = await job_review_service.get_review_status(job_id)
    
    assert result is not None
    assert result["job_id"] == job_id
    assert result["job_title"] == "Senior Developer"
    assert result["job_company"] == "TechCorp"
    assert result["job_status"] == "reviewed"
    assert result["review_exists"] is True
    assert result["review_data"]["recommend"] is True
    assert result["review_data"]["confidence"] == "high"


def test_sample_unit_test():
    """Simple test to verify test framework works."""
    assert 1 + 1 == 2
    assert "job_review" in "test_job_review_service"