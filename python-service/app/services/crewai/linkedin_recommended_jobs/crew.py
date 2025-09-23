"""LinkedIn Recommended Jobs CrewAI implementation with MCP integration.

This crew fetches personalized LinkedIn job recommendations and normalizes them 
to the JobPosting schema. It does NOT perform any recommendation logic, filtering, 
ranking, or evaluation - only data retrieval and normalization.
"""

import asyncio
import json
import logging
from collections.abc import Mapping, Sequence
from json import JSONDecodeError
from threading import Lock, Thread
from typing import Any, Awaitable, Callable, Dict, Optional, List

# Defensive imports with graceful fallback
try:
    from crewai import Agent, Task, Crew, Process
    from crewai.project import CrewBase, agent, task, crew
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Create stub classes for compatibility
    class Agent:
        def __init__(self, **kwargs):
            pass
    class Task:
        def __init__(self, **kwargs):
            pass
    class Crew:
        def __init__(self, **kwargs):
            pass
    class Process:
        sequential = "sequential"
    class CrewBase:
        def __init__(self):
            pass
    def agent(func):
        return func
    def task(func):
        return func
    def crew(func):
        return func

try:
    from app.services.mcp import MCPConfig, MCPToolFactory, MCPToolWrapper
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Create stub classes for compatibility
    class MCPConfig:
        @classmethod
        def from_environment(cls):
            return None
    class MCPToolFactory:
        def __init__(self, adapter):
            pass
        def create_single_crewai_tool(self, tool_name):
            return None
    class MCPToolWrapper:
        def __init__(self, **kwargs):
            pass


_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

_logger = logging.getLogger(__name__)

_MCP_FACTORY: Optional[MCPToolFactory] = None
_MCP_TOOL_CACHE: Dict[str, MCPToolWrapper] = {}
_MCP_LOCK = Lock()

# Tools needed for LinkedIn recommended jobs workflow
_DEFAULT_AGENT_TOOL_MAPPING: Dict[str, Sequence[str]] = {
    "job_collector_agent": ("get_recommended_jobs",),
    "job_details_agent": ("get_job_details",),
    "documentation_agent": (),  # Documentation agent doesn't need MCP tools
}

# JobPosting schema keys for validation
_JOB_POSTING_SCHEMA_KEYS = {
    "title",
    "company", 
    "location",
    "description",
    "url"
}


def _run_coroutine_safely(coro_factory: Callable[[], Awaitable[Any]]) -> Any:
    """Execute an async coroutine, even when an event loop is running."""
    try:
        return asyncio.run(coro_factory())
    except RuntimeError as exc:
        if "asyncio.run() cannot be called from a running event loop" not in str(exc):
            raise

        result: Dict[str, Any] = {}
        error: Optional[BaseException] = None

        def _runner() -> None:
            nonlocal error
            new_loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(new_loop)
                result["value"] = new_loop.run_until_complete(coro_factory())
            except BaseException as thread_exc:
                error = thread_exc
            finally:
                asyncio.set_event_loop(None)
                new_loop.close()

        thread = Thread(target=_runner, daemon=True)
        thread.start()
        thread.join()

        if error is not None:
            raise error

        return result.get("value")


def _get_shared_mcp_factory() -> Optional[MCPToolFactory]:
    """Create or reuse a shared MCP tool factory."""
    global _MCP_FACTORY
    
    # Check if dependencies are available
    if not CREWAI_AVAILABLE or not MCP_AVAILABLE:
        _logger.warning("CrewAI or MCP dependencies not available, MCP factory disabled")
        return None

    if _MCP_FACTORY is not None:
        return _MCP_FACTORY

    with _MCP_LOCK:
        if _MCP_FACTORY is not None:
            return _MCP_FACTORY

        try:
            adapter = MCPConfig.from_environment()
        except Exception as exc:
            _logger.warning("Failed to configure MCP adapter: %s", exc)
            return None

        try:
            is_connected = getattr(adapter, "is_connected", None)
            if callable(is_connected) and is_connected():
                pass
            else:
                _run_coroutine_safely(adapter.connect)
        except Exception as exc:
            _logger.warning("Failed to connect to MCP gateway: %s", exc)
            return None

        _MCP_FACTORY = MCPToolFactory(adapter)
        return _MCP_FACTORY


def _get_or_create_tool_wrapper(
    tool_name: str,
    factory: MCPToolFactory,
) -> Optional[MCPToolWrapper]:
    """Retrieve a cached MCP tool wrapper, creating it if necessary."""
    with _MCP_LOCK:
        wrapper = _MCP_TOOL_CACHE.get(tool_name)
        if wrapper is not None:
            return wrapper

    try:
        wrapper = factory.create_single_crewai_tool(tool_name)
    except Exception as exc:
        _logger.warning("Unable to create MCP tool '%s': %s", tool_name, exc)
        return None

    with _MCP_LOCK:
        existing = _MCP_TOOL_CACHE.setdefault(tool_name, wrapper)
        return existing


def _prepare_agent_tools(
    factory: Optional[MCPToolFactory],
    mapping: Dict[str, Sequence[str]],
) -> Dict[str, Sequence[MCPToolWrapper]]:
    """Build tool assignments for each agent using cached MCP wrappers."""
    if factory is None:
        return {agent_key: tuple() for agent_key in mapping}

    unique_tool_names: list[str] = []
    for names in mapping.values():
        for name in names:
            if name not in unique_tool_names:
                unique_tool_names.append(name)

    available_wrappers: Dict[str, MCPToolWrapper] = {}
    missing_tools: list[str] = []
    for name in unique_tool_names:
        wrapper = _get_or_create_tool_wrapper(name, factory)
        if wrapper is None:
            missing_tools.append(name)
        else:
            available_wrappers[name] = wrapper

    if missing_tools:
        _logger.warning(
            "MCP tools unavailable for LinkedIn recommended jobs crew: %s",
            ", ".join(sorted(set(missing_tools))),
        )

    agent_tools: Dict[str, Sequence[MCPToolWrapper]] = {}
    for agent_key, tool_names in mapping.items():
        agent_tools[agent_key] = tuple(
            available_wrappers[name]
            for name in tool_names
            if name in available_wrappers
        )

    return agent_tools


if CREWAI_AVAILABLE:
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

        def __init__(
            self,
            *,
            mcp_tool_factory: Optional[MCPToolFactory] = None,
            agent_tool_mapping: Optional[Dict[str, Sequence[str]]] = None,
        ):
            """Initialize the crew and prepare MCP tool assignments."""
            super().__init__()
            self._agent_tool_mapping = dict(
                agent_tool_mapping or _DEFAULT_AGENT_TOOL_MAPPING
            )
            self._mcp_tool_factory = mcp_tool_factory or _get_shared_mcp_factory()
            self._agent_tools = _prepare_agent_tools(
                self._mcp_tool_factory,
                self._agent_tool_mapping,
            )

        def _get_agent_tools(self, agent_key: str) -> list[MCPToolWrapper]:
            """Return a copy of the MCP tools assigned to an agent."""
            tools = self._agent_tools.get(agent_key, tuple())
            return list(tools)

        @agent
        def job_collector_agent(self) -> Agent:
            """Agent responsible for collecting LinkedIn job recommendation IDs."""
            return Agent(
                config=self.agents_config["job_collector_agent"],  # type: ignore[index]
                tools=self._get_agent_tools("job_collector_agent"),
            )

        @agent
        def job_details_agent(self) -> Agent:
            """Agent responsible for fetching detailed job information."""
            return Agent(
                config=self.agents_config["job_details_agent"],  # type: ignore[index]
                tools=self._get_agent_tools("job_details_agent"),
            )

        @agent
        def documentation_agent(self) -> Agent:
            """Agent responsible for maintaining project documentation."""
            return Agent(
                config=self.agents_config["documentation_agent"],  # type: ignore[index]
                tools=self._get_agent_tools("documentation_agent"),
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
else:
    # Fallback class when CrewAI is not available
    class LinkedInRecommendedJobsCrew:
        """Fallback crew class when CrewAI is not available."""
        def __init__(self, **kwargs):
            pass
        
        def crew(self):
            raise ImportError("CrewAI is not available. Please install crewai to use this module.")


def get_linkedin_recommended_jobs_crew() -> Crew:
    """Factory function with singleton pattern for crew instances."""
    global _cached_crew
    
    # Check if dependencies are available
    if not CREWAI_AVAILABLE:
        raise ImportError("CrewAI is not available. Please install crewai to use this module.")
    
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
    # Check if dependencies are available
    if not CREWAI_AVAILABLE:
        return {
            "success": False,
            "error_message": "CrewAI is not available. Please install crewai to use this functionality."
        }
    
    crew = get_linkedin_recommended_jobs_crew()
    
    # No inputs needed - fetches recommendations for current logged-in user
    inputs = {}
    
    raw_result = crew.kickoff(inputs=inputs)
    return normalize_linkedin_recommended_jobs_output(raw_result)