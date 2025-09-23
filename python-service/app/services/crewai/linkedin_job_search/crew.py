"""LinkedIn Job Search CrewAI implementation with MCP integration."""

import asyncio
import json
import logging
from collections.abc import Mapping, Sequence
from json import JSONDecodeError
from threading import Lock, Thread
from typing import Any, Awaitable, Callable, Dict, Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

from app.services.mcp import MCPConfig, MCPToolFactory, MCPToolWrapper


_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

_logger = logging.getLogger(__name__)

_MCP_FACTORY: Optional[MCPToolFactory] = None
_MCP_TOOL_CACHE: Dict[str, MCPToolWrapper] = {}
_MCP_LOCK = Lock()

_DEFAULT_AGENT_TOOL_MAPPING: Dict[str, Sequence[str]] = {
    "linkedin_job_searcher": ("linkedin_search",),
    "job_opportunity_analyzer": ("linkedin_search", "profile_lookup"),
    "networking_strategist": ("profile_lookup",),
}

_REPORT_SCHEMA_KEYS = {
    "executive_summary",
    "priority_opportunities",
    "networking_action_plan",
    "timeline_recommendations",
    "success_metrics",
    "linkedin_profile_optimizations",
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
            except BaseException as thread_exc:  # pragma: no cover - defensive
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

    if _MCP_FACTORY is not None:
        return _MCP_FACTORY

    with _MCP_LOCK:
        if _MCP_FACTORY is not None:
            return _MCP_FACTORY

        try:
            adapter = MCPConfig.from_environment()
        except Exception as exc:  # pragma: no cover - configuration issues are logged
            _logger.warning("Failed to configure MCP adapter: %s", exc)
            return None

        try:
            is_connected = getattr(adapter, "is_connected", None)
            if callable(is_connected) and is_connected():
                pass
            else:
                _run_coroutine_safely(adapter.connect)
        except Exception as exc:  # pragma: no cover - connection errors handled gracefully
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
            "MCP tools unavailable for LinkedIn crew: %s",
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


@CrewBase
class LinkedInJobSearchCrew:
    """
    LinkedIn Job Search crew for comprehensive LinkedIn job discovery and analysis.

    This crew follows the standard multi-agent pattern with specialist
    agents coordinated by a manager agent for final synthesis.
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
    def linkedin_job_searcher(self) -> Agent:
        """Specialist agent for LinkedIn job search."""
        return Agent(
            config=self.agents_config["linkedin_job_searcher"],  # type: ignore[index]
            tools=self._get_agent_tools("linkedin_job_searcher"),
        )

    @agent
    def job_opportunity_analyzer(self) -> Agent:
        """Specialist agent for analyzing LinkedIn job opportunities."""
        return Agent(
            config=self.agents_config["job_opportunity_analyzer"],  # type: ignore[index]
            tools=self._get_agent_tools("job_opportunity_analyzer"),
        )

    @agent
    def networking_strategist(self) -> Agent:
        """Specialist agent for LinkedIn networking strategies."""
        return Agent(
            config=self.agents_config["networking_strategist"],  # type: ignore[index]
            tools=self._get_agent_tools("networking_strategist"),
        )

    @agent
    def linkedin_report_writer(self) -> Agent:
        """Manager agent that synthesizes LinkedIn job search results."""
        return Agent(
            config=self.agents_config["linkedin_report_writer"],  # type: ignore[index]
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
    def networking_strategy_task(self) -> Task:
        """Develop networking strategies for LinkedIn opportunities."""
        return Task(
            config=self.tasks_config["networking_strategy_task"],  # type: ignore[index]
            agent=self.networking_strategist(),
            context=[self.linkedin_job_search_task(), self.job_opportunity_analysis_task()],
            async_execution=True
        )

    @task
    def linkedin_report_compilation_task(self) -> Task:
        """Final compilation of LinkedIn job search intelligence."""
        return Task(
            config=self.tasks_config["linkedin_report_compilation_task"],  # type: ignore[index]
            agent=self.linkedin_report_writer(),
            context=[
                self.linkedin_job_search_task(),
                self.job_opportunity_analysis_task(),
                self.networking_strategy_task()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the complete LinkedIn job search crew."""
        return Crew(
            agents=[
                self.linkedin_job_searcher(),
                self.job_opportunity_analyzer(),
                self.networking_strategist()
            ],
            tasks=[
                self.linkedin_job_search_task(),
                self.job_opportunity_analysis_task(),
                self.networking_strategy_task(),
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
    """Execute a LinkedIn job search using the shared crew instance."""

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
    raw_result = crew.kickoff(inputs=inputs)
    return normalize_linkedin_job_search_output(raw_result)
