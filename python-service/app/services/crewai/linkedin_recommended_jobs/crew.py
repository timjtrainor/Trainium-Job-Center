"""LinkedIn Recommended Jobs CrewAI implementation with MCP integration.

This crew fetches personalized LinkedIn job recommendations and normalizes them 
to the JobPosting schema. It does NOT perform any recommendation logic, filtering, 
ranking, or evaluation - only data retrieval and normalization.
"""

import json
import logging
from collections.abc import Mapping
from json import JSONDecodeError
from threading import Lock
from typing import Any, Dict, Optional, List

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai_tools import MCPServerAdapter

_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

_logger = logging.getLogger(__name__)

# JobPosting schema keys for validation
_JOB_POSTING_SCHEMA_KEYS = {
    "title",
    "company", 
    "location",
    "description",
    "url"
}

# MCP Server configuration for the Gateway
_MCP_SERVER_CONFIG = [
    {
        "url": "http://localhost:8811/mcp", 
        "transport": "streamable-http"
    }
]


@CrewBase
class LinkedInRecommendedJobsCrew:
    """
    LinkedIn Recommended Jobs crew for fetching and normalizing LinkedIn job recommendations.
    
    This crew is responsible ONLY for:
    1. Fetching personalized job recommendations from LinkedIn 
    2. Retrieving detailed job posting information
    3. Normalizing data to JobPosting schema
    4. Updating project documentation
    
    It does NOT perform any recommendation logic, filtering, ranking, or job evaluation.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize the crew with MCP tools."""
        super().__init__()
        self._mcp_tools = None
        self._mcp_adapter = None

    def _get_mcp_tools(self):
        """Get MCP tools using MCPServerAdapter."""
        if self._mcp_tools is None:
            try:
                _logger.info("Connecting to MCP Gateway for LinkedIn tools...")
                self._mcp_adapter = MCPServerAdapter(_MCP_SERVER_CONFIG)
                self._mcp_tools = self._mcp_adapter.__enter__()
                _logger.info(f"Available MCP Tools: {[tool.name for tool in self._mcp_tools]}")
            except Exception as e:
                _logger.error(f"Failed to connect to MCP Gateway: {e}")
                self._mcp_tools = []
        return self._mcp_tools

    def _get_linkedin_tools(self):
        """Filter tools to get LinkedIn-specific tools."""
        all_tools = self._get_mcp_tools()
        linkedin_tools = [tool for tool in all_tools if 
                         'recommended' in tool.name.lower() or 
                         'job_details' in tool.name.lower() or
                         'linkedin' in tool.name.lower()]
        return linkedin_tools

    @agent
    def job_collector_agent(self) -> Agent:
        """Agent responsible for collecting LinkedIn job recommendation IDs."""
        return Agent(
            config=self.agents_config["job_collector_agent"],  # type: ignore[index]
            tools=self._get_linkedin_tools(),
        )

    @agent
    def job_details_agent(self) -> Agent:
        """Agent responsible for fetching detailed job information."""
        return Agent(
            config=self.agents_config["job_details_agent"],  # type: ignore[index]
            tools=self._get_linkedin_tools(),
        )

    @agent
    def documentation_agent(self) -> Agent:
        """Agent responsible for maintaining project documentation."""
        return Agent(
            config=self.agents_config["documentation_agent"],  # type: ignore[index]
            tools=[],  # Documentation agent doesn't need MCP tools
        )

    @task
    def collect_recommended_jobs_task(self) -> Task:
        """Task to collect LinkedIn job recommendation IDs."""
        return Task(
            config=self.tasks_config["collect_recommended_jobs_task"],  # type: ignore[index]
            agent=self.job_collector_agent(),
        )

    @task
    def fetch_job_details_task(self) -> Task:
        """Task to fetch detailed job information and normalize to JobPosting schema."""
        return Task(
            config=self.tasks_config["fetch_job_details_task"],  # type: ignore[index]
            agent=self.job_details_agent(),
            context=[self.collect_recommended_jobs_task()]
        )

    @task
    def update_documentation_task(self) -> Task:
        """Task to update project documentation."""
        return Task(
            config=self.tasks_config["update_documentation_task"],  # type: ignore[index]
            agent=self.documentation_agent(),
            context=[self.collect_recommended_jobs_task(), self.fetch_job_details_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the complete LinkedIn recommended jobs crew."""
        return Crew(
            agents=[
                self.job_collector_agent(),
                self.job_details_agent(),
                self.documentation_agent()
            ],
            tasks=[
                self.collect_recommended_jobs_task(),
                self.fetch_job_details_task(),
                self.update_documentation_task()
            ],
            process=Process.sequential,  # Sequential execution as required
            verbose=True,
        )

    def __del__(self):
        """Cleanup MCP adapter when crew is destroyed."""
        if self._mcp_adapter:
            try:
                self._mcp_adapter.__exit__(None, None, None)
            except Exception as e:
                _logger.error(f"Error cleaning up MCP adapter: {e}")


def get_linkedin_recommended_jobs_crew() -> Crew:
    """Factory function with singleton pattern for crew instances."""
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = LinkedInRecommendedJobsCrew().crew()
    assert _cached_crew is not None
    return _cached_crew


def _coerce_to_dict(candidate: Any) -> Optional[Dict[str, Any]]:
    """Attempt to convert various CrewAI output payloads into a dictionary."""
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
        except JSONDecodeError:
            return None

        if isinstance(parsed, Mapping):
            return dict(parsed)

        # Preserve non-mapping JSON payloads for downstream inspection
        return {"data": parsed}

    return None


def _validate_job_posting_schema(job_posting: Dict[str, Any]) -> bool:
    """Validate that a job posting contains all required schema fields."""
    return _JOB_POSTING_SCHEMA_KEYS.issubset(job_posting.keys())


def _ensure_success_flag(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure job posting arrays include a success flag."""
    if "success" not in payload and isinstance(payload.get("data"), list):
        # Check if it looks like an array of job postings
        data = payload.get("data", [])
        if data and all(_validate_job_posting_schema(job) for job in data if isinstance(job, dict)):
            payload = dict(payload)
            payload["success"] = True

    return payload


def normalize_linkedin_recommended_jobs_output(result: Any) -> Dict[str, Any]:
    """Normalize CrewAI outputs into a dictionary for consistent consumption."""
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
    """Execute the LinkedIn recommended jobs crew workflow."""
    crew = get_linkedin_recommended_jobs_crew()
    
    # No inputs needed - fetches recommendations for current logged-in user
    inputs = {}
    
    raw_result = crew.kickoff(inputs=inputs)
    return normalize_linkedin_recommended_jobs_output(raw_result)