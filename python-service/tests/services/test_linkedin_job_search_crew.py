"""Unit tests for LinkedIn Job Search Crew helpers."""
import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.services.mcp.mcp_crewai import BaseTool

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")

from app.services.crewai.linkedin_job_search import crew as linkedin_crew_module
from app.services.crewai.linkedin_job_search.crew import (  # noqa: E402
    LinkedInJobSearchCrew,
    get_linkedin_job_search_crew,
    normalize_linkedin_job_search_output,
    run_linkedin_job_search,
)


def _reset_mcp_state() -> None:
    """Reset crew-level singletons for isolated testing."""

    linkedin_crew_module._cached_crew = None
    linkedin_crew_module._MCP_FACTORY = None
    linkedin_crew_module._MCP_TOOL_CACHE.clear()


class _StubTool(BaseTool):
    """Simple BaseTool implementation for MCP tool assertions."""

    def __init__(self, name: str):
        super().__init__(name=name, description=f"Stub tool for {name}")

    def _run(self, **kwargs):
        return "stub"


@pytest.fixture(autouse=True)
def reset_singletons():
    """Ensure MCP state is reset around each test."""

    _reset_mcp_state()
    yield
    _reset_mcp_state()


class TestLinkedInJobSearchCrew:
    """Test suite covering LinkedIn job search crew behaviour."""

    def test_crew_assembly(self):
        """Crew assembly should include expected agents and tasks."""
        crew_builder = LinkedInJobSearchCrew()
        crew = crew_builder.crew()

        assert len(crew.agents) == 3
        assert len(crew.tasks) == 4

    def test_agents_attach_mcp_tools_with_injected_factory(self):
        """Agents should receive MCP tool wrappers from the factory."""

        search_tool = _StubTool("linkedin_search")
        profile_tool = _StubTool("profile_lookup")

        factory = MagicMock()
        factory.create_single_crewai_tool.side_effect = lambda name: {
            "linkedin_search": search_tool,
            "profile_lookup": profile_tool,
        }[name]

        with (
            patch.object(
                LinkedInJobSearchCrew,
                "map_all_agent_variables",
                return_value=None,
            ),
            patch.object(
                LinkedInJobSearchCrew,
                "map_all_task_variables",
                return_value=None,
            ),
        ):
            crew_builder = LinkedInJobSearchCrew(mcp_tool_factory=factory)

        assert factory.create_single_crewai_tool.call_args_list == [
            call("linkedin_search"),
            call("profile_lookup"),
        ]

        assert crew_builder._agent_tools["linkedin_job_searcher"] == (search_tool,)
        assert crew_builder._agent_tools["job_opportunity_analyzer"] == (
            search_tool,
            profile_tool,
        )
        assert crew_builder._agent_tools["networking_strategist"] == (profile_tool,)

    @patch("app.services.crewai.linkedin_job_search.crew.MCPToolFactory")
    @patch("app.services.crewai.linkedin_job_search.crew.MCPConfig.from_environment")
    def test_default_factory_initialization_uses_environment(
        self,
        mock_from_environment,
        mock_factory_cls,
    ):
        """Crew should configure MCP tooling from environment settings."""

        adapter = MagicMock()
        adapter.is_connected.return_value = False
        adapter.connect = AsyncMock(return_value=None)
        mock_from_environment.return_value = adapter

        search_tool = _StubTool("linkedin_search")
        profile_tool = _StubTool("profile_lookup")

        factory_instance = MagicMock()
        factory_instance.create_single_crewai_tool.side_effect = lambda name: {
            "linkedin_search": search_tool,
            "profile_lookup": profile_tool,
        }[name]
        mock_factory_cls.return_value = factory_instance

        with (
            patch.object(
                LinkedInJobSearchCrew,
                "map_all_agent_variables",
                return_value=None,
            ),
            patch.object(
                LinkedInJobSearchCrew,
                "map_all_task_variables",
                return_value=None,
            ),
        ):
            crew_builder = LinkedInJobSearchCrew()

        mock_from_environment.assert_called_once_with()
        assert adapter.connect.await_count == 1
        mock_factory_cls.assert_called_once_with(adapter)
        assert crew_builder._agent_tools["linkedin_job_searcher"] == (search_tool,)

    @patch("app.services.crewai.linkedin_job_search.crew.MCPConfig.from_environment")
    def test_configuration_failures_disable_mcp_tooling(self, mock_from_environment):
        """If MCP configuration fails, agents should continue without tools."""

        mock_from_environment.side_effect = RuntimeError("config missing")

        with (
            patch.object(
                LinkedInJobSearchCrew,
                "map_all_agent_variables",
                return_value=None,
            ),
            patch.object(
                LinkedInJobSearchCrew,
                "map_all_task_variables",
                return_value=None,
            ),
        ):
            crew_builder = LinkedInJobSearchCrew()

        assert crew_builder._agent_tools["linkedin_job_searcher"] == ()
        assert crew_builder._agent_tools["job_opportunity_analyzer"] == ()
        assert crew_builder._agent_tools["networking_strategist"] == ()

    def test_tool_creation_failures_are_handled_gracefully(self):
        """Tool factory errors should not prevent crew construction."""

        factory = MagicMock()
        factory.create_single_crewai_tool.side_effect = RuntimeError("boom")

        with (
            patch.object(
                LinkedInJobSearchCrew,
                "map_all_agent_variables",
                return_value=None,
            ),
            patch.object(
                LinkedInJobSearchCrew,
                "map_all_task_variables",
                return_value=None,
            ),
        ):
            crew_builder = LinkedInJobSearchCrew(mcp_tool_factory=factory)

        assert crew_builder._agent_tools["linkedin_job_searcher"] == ()
        assert crew_builder._agent_tools["job_opportunity_analyzer"] == ()
        assert crew_builder._agent_tools["networking_strategist"] == ()

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
        mock_payload = {"success": True}
        mock_crew.kickoff.return_value = SimpleNamespace(raw=json.dumps(mock_payload))

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
        mock_payload = {"success": True}
        mock_crew.kickoff.return_value = SimpleNamespace(raw=json.dumps(mock_payload))

        run_linkedin_job_search(keywords="data scientist", remote=False, limit=25)

        kickoff_inputs = mock_crew.kickoff.call_args.kwargs["inputs"]
        assert kickoff_inputs == {
            "keywords": "data scientist",
            "remote": False,
            "limit": 25,
            "search_criteria": "Keywords: 'data scientist'; Limit: 25",
        }

    def test_normalize_injects_success_for_report_schema(self):
        """Report-style payloads should receive a success flag."""
        report_payload = {
            "executive_summary": "Key findings",
            "priority_opportunities": [
                {
                    "rank": 1,
                    "job_title": "Lead Developer",
                    "company_name": "DevSolutions",
                    "rationale": "Matches leadership experience",
                    "next_steps": ["Apply via referral"]
                }
            ],
            "networking_action_plan": ["Connect with alumni"],
            "timeline_recommendations": ["Week 1: outreach"],
            "success_metrics": ["Attend 2 networking events"],
            "linkedin_profile_optimizations": ["Refresh about section"]
        }

        normalized = normalize_linkedin_job_search_output(report_payload)

        assert normalized["success"] is True
        assert normalized["executive_summary"] == "Key findings"
