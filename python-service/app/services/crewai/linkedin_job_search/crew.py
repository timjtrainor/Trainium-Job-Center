"""
LinkedIn Job Search CrewAI implementation.

This crew coordinates LinkedIn job searches using dynamically loaded LinkedIn MCP tools.
"""
import json
from collections.abc import Mapping
from json import JSONDecodeError
from threading import Lock
from typing import Any, Dict, Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from loguru import logger

from ..base import get_linkedin_tools, test_linkedin_mcp_connection_sync


_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

_REPORT_SCHEMA_KEYS = {
    "executive_summary",
    "priority_opportunities",
    "application_recommendations",
    "market_insights",
}

@CrewBase
class LinkedInJobSearchCrew:
    """
    LinkedIn Job Search crew for comprehensive LinkedIn job discovery and analysis.

    This crew follows the standard multi-agent pattern with specialist
    agents coordinated by a manager agent for final synthesis.
    Dynamically loads all LinkedIn MCP tools for comprehensive access.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize crew with LinkedIn MCP tool integration."""
        # Test LinkedIn MCP connection on initialization
        connection_status = test_linkedin_mcp_connection_sync()
        if connection_status.get("success"):
            logger.info(f"LinkedIn MCP connection successful. Found {len(connection_status.get('linkedin_tools', []))} LinkedIn tools")
            if connection_status.get("missing_tools"):
                logger.warning(f"Missing LinkedIn tools: {connection_status.get('missing_tools')}")
        else:
            logger.error(f"LinkedIn MCP connection failed: {connection_status.get('error')}")
        
        # Load LinkedIn tools dynamically
        self._linkedin_tools = get_linkedin_tools()
        logger.info(f"Loaded {len(self._linkedin_tools)} LinkedIn MCP tools for job search crew")

    @agent
    def linkedin_job_searcher(self) -> Agent:
        """Specialist agent for LinkedIn job search with all LinkedIn MCP tools."""
        return Agent(
            config=self.agents_config["linkedin_job_searcher"],  # type: ignore[index]
            tools=self._linkedin_tools,  # Dynamically provide all LinkedIn tools
        )

    @agent
    def job_opportunity_analyzer(self) -> Agent:
        """Specialist agent for analyzing LinkedIn job opportunities with LinkedIn tools."""
        return Agent(
            config=self.agents_config["job_opportunity_analyzer"],  # type: ignore[index]
            tools=self._linkedin_tools,  # Provide LinkedIn tools for company/job research
        )

    @agent
    def linkedin_report_writer(self) -> Agent:
        """Manager agent that synthesizes LinkedIn job search results."""
        return Agent(
            config=self.agents_config["linkedin_report_writer"],  # type: ignore[index]
            tools=self._linkedin_tools,  # Manager can access tools for final validation
        )

    @task
    def linkedin_job_search_task(self) -> Task:
        """Search LinkedIn for relevant job opportunities."""
        return Task(
            config=self.tasks_config["linkedin_job_search_task"],  # type: ignore[index]
            agent=self.linkedin_job_searcher(),
        )

    @task
    def job_opportunity_analysis_task(self) -> Task:
        """Analyze LinkedIn job opportunities for fit and potential."""
        return Task(
            config=self.tasks_config["job_opportunity_analysis_task"],  # type: ignore[index]
            agent=self.job_opportunity_analyzer(),
            context=[self.linkedin_job_search_task()]
        )

    @task
    def linkedin_report_compilation_task(self) -> Task:
        """Final compilation of LinkedIn job search intelligence."""
        return Task(
            config=self.tasks_config["linkedin_report_compilation_task"],  # type: ignore[index]
            agent=self.linkedin_report_writer(),
            context=[
                self.linkedin_job_search_task(),
                self.job_opportunity_analysis_task()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the complete LinkedIn job search crew."""
        return Crew(
            agents=[
                self.linkedin_job_searcher(),
                self.job_opportunity_analyzer()
            ],
            tasks=[
                self.linkedin_job_search_task(),
                self.job_opportunity_analysis_task(),
                self.linkedin_report_compilation_task()
            ],
            process=Process.hierarchical,
            manager_agent=self.linkedin_report_writer(),
            verbose=True,
        )


def get_linkedin_job_search_crew() -> Crew:
    """Factory function with singleton pattern for crew instances."""
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = LinkedInJobSearchCrew().crew()
    assert _cached_crew is not None
    return _cached_crew


def _format_search_criteria(search_params: Dict[str, Any]) -> str:
    """Create a readable description of the LinkedIn job search parameters."""

    keywords = search_params.get("keywords", "")
    parts = [f"Keywords: '{keywords}'" if keywords else "Keywords: ''"]

    location = search_params.get("location")
    if location:
        parts.append(f"Location: {location}")

    filter_parts = []
    if search_params.get("remote"):
        filter_parts.append("Remote only")
    job_type = search_params.get("job_type")
    if job_type:
        filter_parts.append(f"Job type: {job_type}")
    date_posted = search_params.get("date_posted")
    if date_posted:
        filter_parts.append(f"Date posted: {date_posted}")
    experience_level = search_params.get("experience_level")
    if experience_level:
        filter_parts.append(f"Experience level: {experience_level}")

    if filter_parts:
        parts.append("Filters: " + ", ".join(filter_parts))

    limit = search_params.get("limit")
    if limit is not None:
        parts.append(f"Limit: {limit}")

    return "; ".join(parts)


def _build_search_inputs(
    *,
    keywords: str,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    date_posted: Optional[str] = None,
    experience_level: Optional[str] = None,
    remote: bool = False,
    limit: int = 25,
) -> Dict[str, Any]:
    """Prepare crew inputs including a search criteria summary."""

    raw_params: Dict[str, Any] = {
        "keywords": keywords,
        "location": location,
        "job_type": job_type,
        "date_posted": date_posted,
        "experience_level": experience_level,
        "remote": remote,
        "limit": limit,
    }

    search_criteria = _format_search_criteria(raw_params)
    filtered_params = {k: v for k, v in raw_params.items() if v is not None}
    filtered_params["search_criteria"] = search_criteria
    return filtered_params


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

        # Preserve non-mapping JSON payloads for downstream inspection.
        return {"data": parsed}

    return None


def _ensure_success_flag(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure recognized report payloads include a success flag."""

    if "success" not in payload and _REPORT_SCHEMA_KEYS.issubset(payload.keys()):
        payload = dict(payload)
        payload["success"] = True

    return payload


def normalize_linkedin_job_search_output(result: Any) -> Dict[str, Any]:
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


def run_linkedin_job_search(
    *,
    keywords: str,
    location: Optional[str] = None,
    job_type: Optional[str] = None,
    date_posted: Optional[str] = None,
    experience_level: Optional[str] = None,
    remote: bool = False,
    limit: int = 25,
) -> Dict[str, Any]:
    """Execute a LinkedIn job search using the shared crew instance with comprehensive logging."""

    # Test LinkedIn MCP connection before execution
    connection_status = test_linkedin_mcp_connection_sync()
    if not connection_status.get("success"):
        logger.error(f"LinkedIn MCP connection failed before job search: {connection_status.get('error')}")
        return {
            "success": False,
            "error": f"LinkedIn MCP connection failed: {connection_status.get('error')}",
            "connection_status": connection_status
        }

    logger.info(f"LinkedIn job search starting with {len(connection_status.get('linkedin_tools', []))} available LinkedIn tools")
    
    crew = get_linkedin_job_search_crew()
    inputs = _build_search_inputs(
        keywords=keywords,
        location=location,
        job_type=job_type,
        date_posted=date_posted,
        experience_level=experience_level,
        remote=remote,
        limit=limit,
    )
    
    try:
        logger.info(f"Executing LinkedIn job search crew with inputs: {list(inputs.keys())}")
        raw_result = crew.kickoff(inputs=inputs)
        
        # Validate result format
        normalized_result = normalize_linkedin_job_search_output(raw_result)
        
        # Enhanced logging for result validation
        if normalized_result.get("consolidated_jobs"):
            jobs_count = len(normalized_result["consolidated_jobs"])
            logger.info(f"LinkedIn job search completed successfully: {jobs_count} jobs found")
            
            # Validate job data structure
            sample_job = normalized_result["consolidated_jobs"][0] if jobs_count > 0 else {}
            required_fields = ["title", "company", "job_url"]
            missing_fields = [field for field in required_fields if not sample_job.get(field)]
            
            if missing_fields:
                logger.warning(f"Sample job missing required fields: {missing_fields}")
            else:
                logger.info("Job data structure validation passed")
                
        else:
            logger.warning("LinkedIn job search completed but no jobs found in result")
            
        return normalized_result
        
    except Exception as e:
        logger.error(f"LinkedIn job search execution failed: {str(e)}")
        return {
            "success": False,
            "error": f"Job search execution failed: {str(e)}",
            "consolidated_jobs": [],
            "total_jobs": 0
        }
