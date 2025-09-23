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
def test_run_linkedin_recommended_jobs(mock_get_crew: MagicMock) -> None:
    """Crew should be invoked without any external inputs."""

    mock_crew = MagicMock()
    mock_get_crew.return_value = mock_crew
    mock_crew.kickoff.return_value = {"success": True}

    result = run_linkedin_recommended_jobs()

    assert result == {"success": True}
    mock_crew.kickoff.assert_called_once_with(inputs={})


@patch("app.services.crewai.linkedin_recommended_jobs.crew.get_linkedin_recommended_jobs_crew")
def test_run_linkedin_recommended_jobs_error(mock_get_crew: MagicMock) -> None:
    """Errors should be caught and converted into a structured payload."""

    mock_crew = MagicMock()
    mock_get_crew.return_value = mock_crew
    mock_crew.kickoff.side_effect = RuntimeError("gateway unavailable")

    result = run_linkedin_recommended_jobs()

    assert result["success"] is False
    assert "gateway unavailable" in result["error"]
    assert result["metadata"]["context_provided"] is False
    mock_crew.kickoff.assert_called_once_with(inputs={})
