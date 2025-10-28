"""LinkedIn Job Search CrewAI implementation with MCP gateway integration."""

import json
import logging
import os
from collections.abc import Mapping
from json import JSONDecodeError
from threading import Lock
from typing import Any, Dict, Optional

import yaml
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai_tools import MCPServerAdapter

from ..mcp_config import get_mcp_server_config

_logger = logging.getLogger(__name__)

# MCP Server configuration for the Gateway
_MCP_SERVER_CONFIG = get_mcp_server_config()

_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

# Report schema keys for validation
_REPORT_SCHEMA_KEYS = {
    "executive_summary",
    "priority_opportunities", 
    "networking_action_plan",
    "timeline_recommendations",
    "success_metrics",
    "linkedin_profile_optimizations",
}


@CrewBase
class LinkedInJobSearchCrew:
    base_dir = os.path.dirname(__file__)
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    tools_config = os.path.join(base_dir, "config", "tools.yaml")

    def __init__(self):
        super().__init__()
        self._mcp_tools = None
        self._mcp_adapter = None

    def _get_mcp_tools(self):
        """Get MCP tools using MCPServerAdapter."""
        if self._mcp_tools is None:
            try:
                _logger.info(
                    "Connecting to MCP Gateway at %s with transport=%s",
                    _MCP_SERVER_CONFIG[0]["url"],
                    _MCP_SERVER_CONFIG[0]["transport"],
                )
                self._mcp_adapter = MCPServerAdapter(_MCP_SERVER_CONFIG)
                self._mcp_tools = self._mcp_adapter.__enter__()
                _logger.info(
                    "Available MCP Tools: %s",
                    [tool.name for tool in self._mcp_tools],
                )
            except Exception as e:
                _logger.error("Failed to connect to MCP Gateway: %s", e)
                self._mcp_tools = []
        return self._mcp_tools

    def _get_tools_for_agent(self, section: str):
        """Return a filtered set of tools for a specific agent section in tools.yaml."""
        all_tools = self._get_mcp_tools()
        try:
            with open(self.tools_config, "r") as f:
                tool_config = yaml.safe_load(f)
            allowed = {name.lower() for name in tool_config.get(section, [])}
        except Exception as e:
            _logger.error("Failed to load tools.yaml section '%s': %s", section, e)
            return []
        return [tool for tool in all_tools if tool.name.lower() in allowed]

    @agent
    def linkedin_job_searcher(self) -> Agent:
        tools = self._get_tools_for_agent("job_search_tools")
        _logger.info("LinkedIn job searcher tools injected: %s", [t.name for t in tools])
        return Agent(
            config=self.agents_config["linkedin_job_searcher"],  # type: ignore[index]
            tools=tools,
        )

    @agent
    def job_opportunity_analyzer(self) -> Agent:
        tools = self._get_tools_for_agent("analysis_tools")
        _logger.info("Job opportunity analyzer tools injected: %s", [t.name for t in tools])
        return Agent(
            config=self.agents_config["job_opportunity_analyzer"],  # type: ignore[index]
            tools=tools,
        )

    @agent
    def networking_strategist(self) -> Agent:
        tools = self._get_tools_for_agent("networking_tools")
        _logger.info("Networking strategist tools injected: %s", [t.name for t in tools])
        return Agent(
            config=self.agents_config["networking_strategist"],  # type: ignore[index]
            tools=tools,
        )

    @task
    def linkedin_search_task(self) -> Task:
        return Task(
            config=self.tasks_config["linkedin_search_task"],  # type: ignore[index]
            agent=self.linkedin_job_searcher(),
        )

    @task
    def opportunity_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["opportunity_analysis_task"],  # type: ignore[index]
            agent=self.job_opportunity_analyzer(),
        )

    @task
    def networking_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["networking_strategy_task"],  # type: ignore[index]
            agent=self.networking_strategist(),
        )

    @task
    def report_compilation_task(self) -> Task:
        return Task(
            config=self.tasks_config["report_compilation_task"],  # type: ignore[index]
            agent=self.networking_strategist(),  # Use strategist as report writer
            context=[
                self.linkedin_search_task(),
                self.opportunity_analysis_task(),
                self.networking_strategy_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.linkedin_job_searcher(),
                self.job_opportunity_analyzer(),
                self.networking_strategist(),
            ],
            tasks=[
                self.linkedin_search_task(),
                self.opportunity_analysis_task(),
                self.networking_strategy_task(),
                self.report_compilation_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )

    def close(self):
        """Explicitly cleanup MCP adapter."""
        if self._mcp_adapter:
            try:
                self._mcp_adapter.__exit__(None, None, None)
            except Exception as e:
                _logger.error("Error cleaning up MCP adapter: %s", e)


def get_linkedin_job_search_crew() -> Crew:
    """Factory function to create a fresh crew instance per run."""
    return LinkedInJobSearchCrew().crew()


def _coerce_to_dict(candidate: Any) -> Optional[Dict[str, Any]]:
    if candidate is None:
        return None
    if isinstance(candidate, Mapping):
        return dict(candidate)
    if isinstance(candidate, str):
        stripped = candidate.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
        except JSONDecodeError as e:
            _logger.warning(
                "Failed to parse JSON string: %s (error: %s)",
                stripped[:200],
                e,
            )
            return None
        if isinstance(parsed, Mapping):
            return dict(parsed)
        return {"data": parsed}
    return None


def _validate_report_schema(report: Dict[str, Any]) -> bool:
    """Validate that report contains expected schema keys."""
    return _REPORT_SCHEMA_KEYS.issubset(report.keys())


def _ensure_success_flag(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "success" not in payload and isinstance(payload.get("data"), dict):
        data = payload.get("data", {})
        if data and _validate_report_schema(data):
            payload = dict(payload)
            payload["success"] = True
    return payload


def normalize_linkedin_job_search_output(result: Any) -> Dict[str, Any]:
    """Normalize LinkedIn job search crew output to standard format."""
    normalized = _coerce_to_dict(result)
    if normalized is not None:
        return _ensure_success_flag(normalized)
    for attribute in ("raw", "output", "value"):
        if hasattr(result, attribute):
            normalized = _coerce_to_dict(getattr(result, attribute))
            if normalized is not None:
                return _ensure_success_flag(normalized)
    return {}


def run_linkedin_job_search() -> Dict[str, Any]:
    """Run the LinkedIn job search crew and return normalized results."""
    crew = LinkedInJobSearchCrew()
    try:
        raw_result = crew.crew().kickoff(inputs={})
        return normalize_linkedin_job_search_output(raw_result)
    finally:
        crew.close()
