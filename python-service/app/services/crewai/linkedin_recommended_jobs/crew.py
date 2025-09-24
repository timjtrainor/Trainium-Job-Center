"""LinkedIn Recommended Jobs CrewAI implementation with MCP integration.

This crew fetches personalized LinkedIn job recommendations and normalizes them 
to the JobPosting schema. It does NOT perform any recommendation logic, filtering, 
ranking, or evaluation - only data retrieval and normalization.
"""

import json
import logging
import os
from collections.abc import Mapping
from json import JSONDecodeError
from typing import Any, Dict, Optional

import yaml
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai_tools import MCPServerAdapter

_logger = logging.getLogger(__name__)

# JobPosting schema keys for validation
_JOB_POSTING_SCHEMA_KEYS = {
    "title",
    "company",
    "location",
    "description",
    "url",
}

# MCP Server configuration for the Gateway
_MCP_SERVER_CONFIG = [
    {
        "url": "http://mcp-gateway:8811/mcp/",
        "transport": "streamable-http",
        "headers": {
            "Accept": "application/json, text/event-stream"
        }
    }
]


@CrewBase
class LinkedInRecommendedJobsCrew:
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
                with MCPServerAdapter(_MCP_SERVER_CONFIG) as tools:
                    self._mcp_tools = tools
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
    def job_collector_agent(self) -> Agent:
        tools = self._get_tools_for_agent("collector_tools")
        _logger.info("Collector tools injected: %s", [t.name for t in tools])
        return Agent(
            config=self.agents_config["job_collector_agent"],  # type: ignore[index]
            tools=tools,
        )

    @agent
    def job_details_agent(self) -> Agent:
        tools = self._get_tools_for_agent("details_tools")
        _logger.info("Details tools injected: %s", [t.name for t in tools])
        return Agent(
            config=self.agents_config["job_details_agent"],  # type: ignore[index]
            tools=tools,
        )

    @task
    def collect_recommended_jobs_task(self) -> Task:
        return Task(
            config=self.tasks_config["collect_recommended_jobs_task"],  # type: ignore[index]
            agent=self.job_collector_agent(),
        )

    @task
    def fetch_job_details_task(self) -> Task:
        return Task(
            config=self.tasks_config["fetch_job_details_task"],  # type: ignore[index]
            agent=self.job_details_agent(),
            context=[self.collect_recommended_jobs_task()],
        )

    @crew
    def crew(self) -> Crew:
        import os
        verbose_flag = os.getenv("CREW_VERBOSE", "true").lower() == "true"
        return Crew(
            agents=[self.job_collector_agent(), self.job_details_agent()],
            tasks=[self.collect_recommended_jobs_task(), self.fetch_job_details_task()],
            process=Process.sequential,
            verbose=verbose_flag,
        )

    def close(self):
        """Explicitly cleanup MCP adapter."""
        if self._mcp_adapter:
            try:
                self._mcp_adapter.__exit__(None, None, None)
            except Exception as e:
                _logger.error("Error cleaning up MCP adapter: %s", e)


def get_linkedin_recommended_jobs_crew() -> Crew:
    """Factory function to create a fresh crew instance per run."""
    return LinkedInRecommendedJobsCrew().crew()


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


def _validate_job_posting_schema(job_posting: Dict[str, Any]) -> bool:
    if not _JOB_POSTING_SCHEMA_KEYS.issubset(job_posting.keys()):
        return False
    checks = {
        "title": str,
        "company": str,
        "location": str,
        "description": str,
        "url": str,
    }
    for field, expected_type in checks.items():
        if not isinstance(job_posting.get(field), expected_type):
            return False
    return True


def _ensure_success_flag(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "success" not in payload and isinstance(payload.get("data"), list):
        data = payload.get("data", [])
        if data and all(
            _validate_job_posting_schema(job) for job in data if isinstance(job, dict)
        ):
            payload = dict(payload)
            payload["success"] = True
    return payload


def normalize_linkedin_recommended_jobs_output(result: Any) -> Dict[str, Any]:
    normalized = _coerce_to_dict(result)
    if normalized is not None:
        return _ensure_success_flag(normalized)
    for attribute in ("raw", "output", "value"):
        if hasattr(result, attribute):
            normalized = _coerce_to_dict(getattr(result, attribute))
            if normalized is not None:
                return _ensure_success_flag(normalized)
    return {}


def run_linkedin_recommended_jobs() -> Dict[str, Any]:
    crew = LinkedInRecommendedJobsCrew()
    try:
        raw_result = crew.crew().kickoff(inputs={})
        return normalize_linkedin_recommended_jobs_output(raw_result)
    finally:
        crew.close()