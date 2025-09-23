"""API tests for LinkedIn recommended jobs endpoint."""

from __future__ import annotations

import os
from typing import Any, Dict
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")
os.environ.pop("LINKEDIN_RECOMMENDED_PROFILE_URL", None)

from app.api.v1.endpoints.linkedin_recommended_jobs import router  # noqa: E402

api_app = FastAPI()
api_app.include_router(router, prefix="/crewai")
client = TestClient(api_app)


def _build_fake_result(success: bool = True) -> Dict[str, Any]:
    """Helper to construct fake crew results for testing."""

    if success:
        return {
            "success": True,
            "recommended_jobs": [
                {
                    "job_title": "Staff Engineer",
                    "company_name": "InnovateX",
                    "job_url": "https://linkedin.com/jobs/view/123",
                    "priority": "high",
                }
            ],
            "metadata": {"profile_context_used": False},
            "summary": "Top matches ready for outreach",
        }

    return {
        "success": False,
        "error": "No recommendations available",
        "recommended_jobs": [],
    }


@patch("app.api.v1.endpoints.linkedin_recommended_jobs.run_linkedin_recommended_jobs")
def test_generate_recommended_jobs_without_profile_url(mock_run: MagicMock) -> None:
    """Endpoint should succeed when no profile URL is provided."""

    mock_run.return_value = _build_fake_result(success=True)

    payload = {
        "user_id": "user-123",
        "job_preferences": ["engineering leadership"],
        "target_companies": ["InnovateX"],
        "limit": 3,
    }

    if "LINKEDIN_RECOMMENDED_PROFILE_URL" in os.environ:
        del os.environ["LINKEDIN_RECOMMENDED_PROFILE_URL"]

    response = client.post("/crewai/linkedin-recommended-jobs", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["metadata"]["profile_context_used"] is False

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert kwargs["profile_url"] is None
    assert "profile_url" not in args[0]


@patch("app.api.v1.endpoints.linkedin_recommended_jobs.run_linkedin_recommended_jobs")
def test_generate_recommended_jobs_with_profile_url(mock_run: MagicMock) -> None:
    """Profile URL should be forwarded when provided explicitly."""

    mock_run.return_value = _build_fake_result(success=True)

    payload = {
        "user_id": "user-456",
        "profile_url": "https://www.linkedin.com/in/example",
        "limit": 5,
        "include_remote": True,
    }

    response = client.post("/crewai/linkedin-recommended-jobs", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert kwargs["profile_url"] == "https://www.linkedin.com/in/example"
    assert "profile_url" not in args[0]


@patch("app.api.v1.endpoints.linkedin_recommended_jobs.run_linkedin_recommended_jobs")
def test_generate_recommended_jobs_failure(mock_run: MagicMock) -> None:
    """Crew failures should be surfaced as error responses."""

    mock_run.return_value = _build_fake_result(success=False)

    payload = {
        "user_id": "user-789",
        "limit": 2,
    }

    response = client.post("/crewai/linkedin-recommended-jobs", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert "No recommendations available" in body["message"]

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert kwargs["profile_url"] is None
    assert "profile_url" not in args[0]
