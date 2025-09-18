"""Unit tests for LinkedIn Job Search Crew helpers."""
import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")

from app.services.crewai.linkedin_job_search.crew import (  # noqa: E402
    LinkedInJobSearchCrew,
    get_linkedin_job_search_crew,
    run_linkedin_job_search,
)


class TestLinkedInJobSearchCrew:
    """Test suite covering LinkedIn job search crew behaviour."""

    def test_crew_assembly(self):
        """Crew assembly should include expected agents and tasks."""
        crew_builder = LinkedInJobSearchCrew()
        crew = crew_builder.crew()

        assert len(crew.agents) == 3
        assert len(crew.tasks) == 4

    def test_get_linkedin_job_search_crew_singleton(self):
        """Factory should return the same crew instance."""
        crew_one = get_linkedin_job_search_crew()
        crew_two = get_linkedin_job_search_crew()

        assert crew_one is crew_two

    @patch("app.services.crewai.linkedin_job_search.crew.get_linkedin_job_search_crew")
    def test_run_linkedin_job_search_includes_search_criteria(self, mock_get_crew):
        """run_linkedin_job_search should pass readable criteria to the crew."""
        mock_crew = MagicMock()
        mock_get_crew.return_value = mock_crew
        mock_crew.kickoff.return_value = {"success": True}

        result = run_linkedin_job_search(
            keywords="python developer",
            location="Remote",
            job_type="full-time",
            experience_level="senior",
            remote=True,
            limit=10,
        )

        assert result == {"success": True}
        mock_crew.kickoff.assert_called_once()
        kickoff_inputs = mock_crew.kickoff.call_args.kwargs["inputs"]
        assert kickoff_inputs == {
            "keywords": "python developer",
            "location": "Remote",
            "job_type": "full-time",
            "experience_level": "senior",
            "remote": True,
            "limit": 10,
            "search_criteria": (
                "Keywords: 'python developer'; Location: Remote; "
                "Filters: Remote only, Job type: full-time, Experience level: senior; Limit: 10"
            ),
        }

    @patch("app.services.crewai.linkedin_job_search.crew.get_linkedin_job_search_crew")
    def test_run_linkedin_job_search_handles_optional_fields(self, mock_get_crew):
        """Optional filters should be omitted from inputs and description when missing."""
        mock_crew = MagicMock()
        mock_get_crew.return_value = mock_crew
        mock_crew.kickoff.return_value = {"success": True}

        run_linkedin_job_search(keywords="data scientist", remote=False, limit=25)

        kickoff_inputs = mock_crew.kickoff.call_args.kwargs["inputs"]
        assert kickoff_inputs == {
            "keywords": "data scientist",
            "remote": False,
            "limit": 25,
            "search_criteria": "Keywords: 'data scientist'; Limit: 25",
        }
