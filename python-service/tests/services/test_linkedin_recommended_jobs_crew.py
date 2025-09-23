"""Unit tests for LinkedIn recommended jobs crew helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.crewai.linkedin_recommended_jobs.crew import (
    get_linkedin_recommended_jobs_crew,
    run_linkedin_recommended_jobs,
)


def test_get_linkedin_recommended_jobs_crew_singleton() -> None:
    """Factory should return the same crew instance across calls."""

    crew_one = get_linkedin_recommended_jobs_crew()
    crew_two = get_linkedin_recommended_jobs_crew()
    assert crew_one is crew_two


@patch("app.services.crewai.linkedin_recommended_jobs.crew.get_linkedin_recommended_jobs_crew")
def test_run_linkedin_recommended_jobs_without_profile(mock_get_crew: MagicMock) -> None:
    """Profile URL should be stripped from payload when absent."""

    mock_crew = MagicMock()
    mock_get_crew.return_value = mock_crew
    mock_crew.kickoff.return_value = {"success": True}

    payload = {"user_id": "user-123", "profile_url": "https://old.example"}
    result = run_linkedin_recommended_jobs(payload, profile_url=None)

    assert result == {"success": True}
    mock_crew.kickoff.assert_called_once()
    kickoff_inputs = mock_crew.kickoff.call_args.kwargs["inputs"]
    assert "profile_url" not in kickoff_inputs


@patch("app.services.crewai.linkedin_recommended_jobs.crew.get_linkedin_recommended_jobs_crew")
def test_run_linkedin_recommended_jobs_with_profile(mock_get_crew: MagicMock) -> None:
    """Provided profile URL should be included in payload."""

    mock_crew = MagicMock()
    mock_get_crew.return_value = mock_crew
    mock_crew.kickoff.return_value = {"success": True}

    payload = {"user_id": "user-456"}
    result = run_linkedin_recommended_jobs(payload, profile_url="https://linkedin.com/in/test")

    assert result == {"success": True}
    kickoff_inputs = mock_crew.kickoff.call_args.kwargs["inputs"]
    assert kickoff_inputs["profile_url"] == "https://linkedin.com/in/test"


@patch("app.services.crewai.linkedin_recommended_jobs.crew.get_linkedin_recommended_jobs_crew")
def test_run_linkedin_recommended_jobs_error(mock_get_crew: MagicMock) -> None:
    """Errors should be caught and converted into a structured payload."""

    mock_crew = MagicMock()
    mock_get_crew.return_value = mock_crew
    mock_crew.kickoff.side_effect = RuntimeError("gateway unavailable")

    result = run_linkedin_recommended_jobs({"user_id": "user-789"})

    assert result["success"] is False
    assert "gateway unavailable" in result["error"]
    assert result["metadata"]["profile_url_provided"] is False
