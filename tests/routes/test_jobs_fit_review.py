"""Tests for the job posting fit review route."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from python_service.app.main import app
from python_service.app.models.job_posting import JobPosting
from python_service.app.models.fit_review import FitReviewResult


@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_job_posting():
    """Sample job posting data for testing."""
    return {
        "title": "Senior Python Developer",
        "company": "Tech Innovations Inc",
        "location": "San Francisco, CA", 
        "description": "We are looking for a senior Python developer with expertise in FastAPI and CrewAI.",
        "url": "https://example.com/jobs/senior-python-dev"
    }


@pytest.fixture
def sample_fit_review_result():
    """Sample fit review result for mocking."""
    return {
        "job_id": "job_123456789",
        "final": {
            "recommend": True,
            "rationale": "Strong technical fit with growth opportunities",
            "confidence": "high"
        },
        "personas": [
            {
                "id": "technical_leader",
                "recommend": True,
                "reason": "Excellent technical alignment with requirements",
                "notes": ["Modern tech stack", "Remote-friendly"],
                "sources": ["job_description", "company_research"]
            }
        ],
        "tradeoffs": ["Work-life balance vs high growth potential"],
        "actions": ["Research company culture", "Prepare technical questions"],
        "sources": ["job_description", "company_website", "glassdoor"]
    }


@patch("python_service.app.services.crewai.job_posting_review.crew.run_crew")
def test_fit_review_200_ok(mock_run_crew, client, sample_job_posting, sample_fit_review_result):
    """Test successful job posting fit review."""
    # Mock run_crew to return valid FitReviewResult
    mock_run_crew.return_value = sample_fit_review_result
    
    # Make request
    response = client.post("/jobs/posting/fit_review", json=sample_job_posting)
    
    # Assert response
    assert response.status_code == 200
    
    # Verify response structure matches FitReviewResult
    result = response.json()
    assert "job_id" in result
    assert "final" in result
    assert "personas" in result
    assert "tradeoffs" in result
    assert "actions" in result
    assert "sources" in result
    
    # Verify final recommendation structure
    final = result["final"]
    assert "recommend" in final
    assert "rationale" in final
    assert "confidence" in final
    assert isinstance(final["recommend"], bool)
    
    # Verify personas structure
    personas = result["personas"]
    assert isinstance(personas, list)
    assert len(personas) > 0
    
    for persona in personas:
        assert "id" in persona
        assert "recommend" in persona
        assert "reason" in persona
    
    # Verify run_crew was called with correct parameters
    mock_run_crew.assert_called_once()
    call_args = mock_run_crew.call_args
    
    # Check that job posting data was passed
    job_data = call_args[0][0]  # First positional argument
    assert job_data["title"] == sample_job_posting["title"]
    assert job_data["company"] == sample_job_posting["company"]
    
    # Check that correlation_id was passed
    correlation_id = call_args[1]["correlation_id"]  # Keyword argument
    assert correlation_id is not None
    assert len(correlation_id) == 36  # UUID format


@patch("python_service.app.services.crewai.job_posting_review.crew.run_crew")
def test_fit_review_500_on_exception(mock_run_crew, client, sample_job_posting):
    """Test error handling when run_crew raises an exception."""
    # Mock run_crew to raise an exception
    mock_run_crew.side_effect = Exception("Crew execution failed")
    
    # Make request
    response = client.post("/jobs/posting/fit_review", json=sample_job_posting)
    
    # Assert error response
    assert response.status_code == 500
    
    # Verify error response structure
    error_detail = response.json()["detail"]
    assert error_detail["error"] == "fit_review_failed"
    assert "correlation_id" in error_detail
    assert len(error_detail["correlation_id"]) == 36  # UUID format
    
    # Verify run_crew was called
    mock_run_crew.assert_called_once()


def test_validation_422_missing_fields(client):
    """Test validation error for missing required fields."""
    # Request with missing required fields
    incomplete_job = {
        "title": "Senior Python Developer",
        # Missing company, location, description, url
    }
    
    response = client.post("/jobs/posting/fit_review", json=incomplete_job)
    
    # Assert validation error
    assert response.status_code == 422
    
    # Verify error details contain field validation information
    error_detail = response.json()
    assert "detail" in error_detail
    
    # Should have validation errors for missing fields
    detail = error_detail["detail"]
    missing_fields = [error["loc"][-1] for error in detail]
    
    expected_missing = {"company", "location", "description", "url"}
    actual_missing = set(missing_fields)
    
    assert expected_missing.issubset(actual_missing)


def test_validation_422_invalid_url(client):
    """Test validation error for invalid URL format."""
    # Request with invalid URL
    invalid_job = {
        "title": "Senior Python Developer",
        "company": "Tech Innovations Inc",
        "location": "San Francisco, CA",
        "description": "We are looking for a senior Python developer.",
        "url": "not-a-valid-url"
    }
    
    response = client.post("/jobs/posting/fit_review", json=invalid_job)
    
    # Assert validation error
    assert response.status_code == 422
    
    # Verify error details mention URL validation
    error_detail = response.json()
    detail = error_detail["detail"]
    
    # Check that URL validation error is present
    url_errors = [error for error in detail if error["loc"][-1] == "url"]
    assert len(url_errors) > 0


@patch("python_service.app.services.crewai.job_posting_review.crew.run_crew")
def test_options_parameter_passed_through(mock_run_crew, client, sample_job_posting, sample_fit_review_result):
    """Test that options parameter is passed through to run_crew."""
    mock_run_crew.return_value = sample_fit_review_result
    
    # Add options to the request
    request_with_options = {
        **sample_job_posting,
        "options": {"mock_mode": True, "debug": True}
    }
    
    response = client.post("/jobs/posting/fit_review", json=request_with_options)
    
    assert response.status_code == 200
    
    # Verify options were passed to run_crew
    mock_run_crew.assert_called_once()
    call_args = mock_run_crew.call_args
    
    # Check options parameter
    options = call_args[1]["options"]  # Keyword argument
    assert options is not None


@patch("python_service.app.services.crewai.job_posting_review.crew.run_crew")
def test_correlation_id_in_logs(mock_run_crew, client, sample_job_posting, sample_fit_review_result, caplog):
    """Test that correlation_id appears in log messages."""
    mock_run_crew.return_value = sample_fit_review_result
    
    # Make request
    response = client.post("/jobs/posting/fit_review", json=sample_job_posting)
    
    assert response.status_code == 200
    
    # Check that logs contain correlation_id
    log_messages = [record.message for record in caplog.records]
    request_logs = [msg for msg in log_messages if "correlation_id" in msg]

    # Should have entry and exit logs with correlation_id
    assert len(request_logs) >= 2


@patch("python_service.app.services.crewai.job_posting_review.crew.run_crew")
def test_validation_error_returns_500_without_logging_keyerror(
    mock_run_crew, client, sample_job_posting, caplog
):
    """Regression test for logging KeyError on validation errors."""
    # Return data that fails FitReviewResult validation
    mock_run_crew.return_value = {"invalid": "data"}

    response = client.post("/jobs/posting/fit_review", json=sample_job_posting)

    # Route should handle validation errors and return structured 500
    assert response.status_code == 500
    error_detail = response.json()["detail"]
    assert error_detail["error"] == "fit_review_failed"
    assert "correlation_id" in error_detail

    # Ensure logging did not raise a KeyError
    log_messages = "".join(record.message for record in caplog.records)
    assert "KeyError" not in log_messages