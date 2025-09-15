"""
Tests for job review worker function.
"""
import asyncio
import os
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app.services.infrastructure.worker import process_job_review


def test_process_job_review_with_mock():
    """Test job review worker with mocked dependencies."""
    job_id = str(uuid4())
    
    # Mock successful job data
    mock_job_data = {
        "id": job_id,
        "title": "Python Developer",
        "company": "TechCorp",
        "description": "Great Python role with AI focus",
        "job_url": "https://example.com/job/123"
    }
    
    # Mock successful CrewAI response
    mock_crew_result = {
        "final": {
            "recommend": True,
            "confidence": "high",
            "rationale": "Excellent match for Python/AI skills"
        },
        "personas": [
            {"id": "developer", "recommend": True, "reason": "Tech stack match"}
        ],
        "tradeoffs": [],
        "actions": ["Apply immediately"],
        "sources": ["job_description", "company_analysis"]
    }
    
    with patch('app.services.infrastructure.worker.get_database_service') as mock_get_db, \
         patch('app.services.crewai.job_posting_review.crew.run_crew') as mock_run_crew:
        
        # Setup database service mock
        mock_db_service = Mock()
        mock_db_service.initialized = True
        mock_db_service.initialize = AsyncMock(return_value=True)
        mock_db_service.update_job_status = AsyncMock(return_value=True)
        mock_db_service.get_job_by_id = AsyncMock(return_value=mock_job_data)
        mock_db_service.get_job_review = AsyncMock(return_value=None)  # No existing review
        mock_db_service.insert_job_review = AsyncMock(return_value=True)
        mock_get_db.return_value = mock_db_service
        
        # Setup CrewAI mock
        mock_run_crew.return_value = mock_crew_result
        
        # Mock asyncio event loop
        with patch('asyncio.get_event_loop') as mock_get_loop, \
             patch('asyncio.new_event_loop') as mock_new_loop, \
             patch('asyncio.set_event_loop') as mock_set_loop:
            
            mock_loop = Mock()
            mock_loop.run_until_complete = Mock(side_effect=lambda coro: asyncio.run(coro))
            mock_get_loop.return_value = mock_loop
            
            # Execute the worker function
            result = process_job_review(job_id, max_retries=3)
        
        # Verify result
        assert result["status"] == "completed"
        assert result["job_id"] == job_id
        assert result["recommend"] is True
        assert result["confidence"] == "high"
        assert "processing_time_seconds" in result
        
        # Verify database interactions
        mock_db_service.get_job_by_id.assert_called()
        mock_db_service.update_job_status.assert_called()
        mock_db_service.insert_job_review.assert_called()
        
        # Verify CrewAI was called
        mock_run_crew.assert_called_once()


def test_process_job_review_handles_decimal_salary_fields():
    """Ensure Decimal salary fields are coerced before crew execution."""
    job_id = str(uuid4())
    decimal_min = Decimal("70000.50")
    decimal_max = Decimal("90000.75")

    mock_job_data = {
        "id": job_id,
        "title": "Backend Engineer",
        "company": "DataWorks",
        "description": "Work on robust APIs",
        "min_amount": decimal_min,
        "max_amount": decimal_max,
        "currency": "USD",
        "interval": "year",
    }

    mock_crew_result = {
        "final": {
            "recommend": True,
            "confidence": "medium",
            "rationale": "Salary range is competitive",
        },
        "personas": [],
        "tradeoffs": [],
        "actions": [],
        "sources": [],
    }

    with patch('app.services.infrastructure.worker.get_database_service') as mock_get_db, \
         patch('app.services.crewai.job_posting_review.crew.run_crew') as mock_run_crew:

        mock_db_service = Mock()
        mock_db_service.initialized = True
        mock_db_service.initialize = AsyncMock(return_value=True)
        mock_db_service.update_job_status = AsyncMock(return_value=True)
        mock_db_service.get_job_by_id = AsyncMock(return_value=mock_job_data)
        mock_db_service.get_job_review = AsyncMock(return_value=None)
        mock_db_service.insert_job_review = AsyncMock(return_value=True)
        mock_get_db.return_value = mock_db_service

        mock_run_crew.return_value = mock_crew_result

        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_loop.run_until_complete = Mock(side_effect=lambda coro: asyncio.run(coro))
            mock_get_loop.return_value = mock_loop

            result = process_job_review(job_id, max_retries=3)

    assert result["status"] == "completed"
    mock_run_crew.assert_called_once()

    crew_payload = mock_run_crew.call_args[0][0]
    assert isinstance(crew_payload["salary_info"]["min_amount"], float)
    assert isinstance(crew_payload["salary_info"]["max_amount"], float)
    assert crew_payload["salary_info"]["min_amount"] == float(decimal_min)
    assert crew_payload["salary_info"]["max_amount"] == float(decimal_max)


def test_process_job_review_logs_processing_message():
    """Ensure worker logs the expected processing message and completes."""
    job_id = str(uuid4())

    mock_job_data = {
        "id": job_id,
        "title": "Data Scientist",
        "company": "Insight Analytics",
        "description": "Analyze large datasets",
    }

    mock_crew_result = {
        "final": {
            "recommend": True,
            "confidence": "medium",
            "rationale": "Strong analytics fit",
        },
        "personas": [],
        "tradeoffs": [],
        "actions": [],
        "sources": [],
    }

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        with patch('app.services.infrastructure.worker.get_database_service') as mock_get_db, \
             patch('app.services.crewai.job_posting_review.crew.run_crew') as mock_run_crew, \
             patch('app.services.infrastructure.worker.logger') as mock_logger:

            mock_db_service = Mock()
            mock_db_service.initialized = True
            mock_db_service.initialize = AsyncMock(return_value=True)
            mock_db_service.update_job_status = AsyncMock(return_value=True)
            mock_db_service.get_job_by_id = AsyncMock(return_value=mock_job_data)
            mock_db_service.get_job_review = AsyncMock(return_value=None)
            mock_db_service.insert_job_review = AsyncMock(return_value=True)
            mock_get_db.return_value = mock_db_service

            mock_run_crew.return_value = mock_crew_result

            result = process_job_review(job_id, max_retries=2)

        mock_logger.info.assert_any_call(f"Processing job review for job_id: {job_id}")
        assert result["status"] == "completed"
        assert result["job_id"] == job_id
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def test_process_job_review_job_not_found():
    """Test worker behavior when job is not found."""
    job_id = str(uuid4())
    
    with patch('app.services.infrastructure.worker.get_database_service') as mock_get_db:
        mock_db_service = Mock()
        mock_db_service.initialized = True
        mock_db_service.initialize = AsyncMock(return_value=True)
        mock_db_service.update_job_status = AsyncMock(return_value=True)
        mock_db_service.get_job_by_id = AsyncMock(return_value=None)  # Job not found
        mock_get_db.return_value = mock_db_service
        
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_loop.run_until_complete = Mock(side_effect=lambda coro: asyncio.run(coro))
            mock_get_loop.return_value = mock_loop
            
            result = process_job_review(job_id)
        
        assert result["status"] == "failed"
        assert "Job not found" in result["message"]


def test_process_job_review_crew_error():
    """Test worker behavior when CrewAI returns an error."""
    job_id = str(uuid4())
    
    mock_job_data = {
        "id": job_id,
        "title": "Test Job",
        "company": "Test Corp",
        "description": "Test description"
    }
    
    # Mock CrewAI error response
    mock_crew_result = {
        "error": "CrewAI processing failed due to timeout"
    }
    
    with patch('app.services.infrastructure.worker.get_database_service') as mock_get_db, \
         patch('app.services.crewai.job_posting_review.crew.run_crew') as mock_run_crew:
        
        mock_db_service = Mock()
        mock_db_service.initialized = True
        mock_db_service.initialize = AsyncMock(return_value=True)
        mock_db_service.update_job_status = AsyncMock(return_value=True)
        mock_db_service.get_job_by_id = AsyncMock(return_value=mock_job_data)
        mock_db_service.get_job_review = AsyncMock(return_value=None)
        mock_db_service.insert_job_review = AsyncMock(return_value=True)
        mock_get_db.return_value = mock_db_service
        
        mock_run_crew.return_value = mock_crew_result
        
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_loop.run_until_complete = Mock(side_effect=lambda coro: asyncio.run(coro))
            mock_get_loop.return_value = mock_loop
            
            result = process_job_review(job_id, max_retries=3)
        
        # Should return retry status for first attempt
        assert result["status"] == "retry"
        assert "will retry" in result["message"]
        assert result["retry_count"] == 1


def test_job_review_max_retries_reached():
    """Test worker behavior when max retries are reached."""
    job_id = str(uuid4())
    
    # Mock existing review with high retry count
    mock_existing_review = {
        "retry_count": 3  # At max retries
    }
    
    with patch('app.services.infrastructure.worker.get_database_service') as mock_get_db:
        mock_db_service = Mock()
        mock_db_service.initialized = True
        mock_db_service.initialize = AsyncMock(return_value=True)
        mock_db_service.update_job_status = AsyncMock(return_value=True)
        mock_db_service.get_job_by_id = AsyncMock(return_value={
            "title": "Retry Blocked",
            "company": "Retry Inc",
            "description": "",
        })
        mock_db_service.get_job_review = AsyncMock(return_value=mock_existing_review)
        mock_db_service.insert_job_review = AsyncMock(return_value=True)
        mock_get_db.return_value = mock_db_service
        
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_loop.run_until_complete = Mock(side_effect=lambda coro: asyncio.run(coro))
            mock_get_loop.return_value = mock_loop
            
            result = process_job_review(job_id, max_retries=3)
        
        assert result["status"] == "failed"
        assert "Maximum retry attempts" in result["message"]
        assert result["retry_count"] == 3


def test_simple_worker_import():
    """Test that worker module can be imported without errors."""
    from app.services.infrastructure.worker import process_job_review
    assert callable(process_job_review)