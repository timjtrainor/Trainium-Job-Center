"""LinkedIn recommended jobs crew using MCP-powered tools."""
from __future__ import annotations

import json
import logging
from json import JSONDecodeError
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from app.services.crewai.tools.mcp_tools import (
    LINKEDIN_COMPANY_PROFILE_TOOL_NAME,
    LINKEDIN_JOB_DETAILS_TOOL_NAME,
    LINKEDIN_PROFILE_LOOKUP_TOOL_NAME,
    LINKEDIN_RECOMMENDED_JOBS_TOOL_NAME,
    MCPToolsManager,
)

LOGGER = logging.getLogger(__name__)
_OUTPUT_DIR = Path(__file__).resolve().parent


_DEFAULT_ALIAS_MAPPING: Dict[str, Sequence[str]] = {
    LINKEDIN_RECOMMENDED_JOBS_TOOL_NAME: ("get_recommended_jobs",),
    LINKEDIN_JOB_DETAILS_TOOL_NAME: ("get_job_details",),
    LINKEDIN_PROFILE_LOOKUP_TOOL_NAME: ("linkedin_profile_lookup", "person_lookup"),
    LINKEDIN_COMPANY_PROFILE_TOOL_NAME: ("company_profile_lookup", "linkedin_company_lookup"),
}


_cached_crew: Optional[Crew] = None
_crew_lock = Lock()


def _filter_inputs(**kwargs: Any) -> Dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value is not None}


def _coerce_to_dict(candidate: Any) -> Optional[Dict[str, Any]]:
    if candidate is None:
        return None

    if isinstance(candidate, Mapping):
        return dict(candidate)

    if isinstance(candidate, str):
        text = candidate.strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except JSONDecodeError:
            return None
        return parsed if isinstance(parsed, Mapping) else {"data": parsed}

    for attribute in ("raw", "output", "value"):
        if hasattr(candidate, attribute):
            nested = getattr(candidate, attribute)
            mapping = _coerce_to_dict(nested)
            if mapping is not None:
                return mapping

    return None


def _default_payload() -> Dict[str, Any]:
    return {
        "success": False,
        "discovered_jobs": [],
        "enriched_jobs": [],
        "metadata": {},
    }


def normalize_linkedin_recommended_jobs_output(result: Any) -> Dict[str, Any]:
    payload = _coerce_to_dict(result) or _default_payload()

    payload.setdefault("discovered_jobs", [])
    payload.setdefault("enriched_jobs", [])
    payload.setdefault("metadata", {})

    if "success" not in payload:
        payload["success"] = bool(payload.get("enriched_jobs")) or bool(payload.get("discovered_jobs"))

    return payload


def write_recommended_job_outputs(result: Mapping[str, Any]) -> None:
    discovered = result.get("discovered_jobs")
    if discovered:
        try:
            (_OUTPUT_DIR / "discovered_jobs.json").write_text(
                json.dumps(discovered, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:  # pragma: no cover - filesystem best effort
            LOGGER.warning("Unable to write discovered jobs file: %s", exc)

    enriched = result.get("enriched_jobs")
    if enriched:
        try:
            (_OUTPUT_DIR / "enriched_jobs.json").write_text(
                json.dumps(enriched, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:  # pragma: no cover - filesystem best effort
            LOGGER.warning("Unable to write enriched jobs file: %s", exc)


@CrewBase
class LinkedInRecommendedJobsCrew:
    """Crew orchestrating LinkedIn recommended jobs discovery and enrichment."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, *, tools_manager: Optional[MCPToolsManager] = None):
        super().__init__()
        self._tools_manager = tools_manager or MCPToolsManager()
        self._agent_tools: Dict[str, Sequence[Any]] = {
            "job_discovery_agent": self._resolve_tools(
                [LINKEDIN_RECOMMENDED_JOBS_TOOL_NAME]
            ),
            "job_enrichment_agent": self._resolve_tools(
                [
                    LINKEDIN_JOB_DETAILS_TOOL_NAME,
                    LINKEDIN_PROFILE_LOOKUP_TOOL_NAME,
                    LINKEDIN_COMPANY_PROFILE_TOOL_NAME,
                ]
            ),
        }

    def _resolve_tools(self, tool_names: Iterable[str]) -> Sequence[Any]:
        alias_mapping = {name: _DEFAULT_ALIAS_MAPPING.get(name, tuple()) for name in tool_names}
        tools = self._tools_manager.get_tools(tuple(tool_names), alias_mapping=alias_mapping)
        if not tools:
            LOGGER.warning("No MCP tools available for names: %s", ", ".join(tool_names))
        return tuple(tools)

    def close(self) -> None:
        self._tools_manager.close()

    def __del__(self) -> None:  # pragma: no cover - defensive cleanup
        try:
            self.close()
        except Exception:
            pass

    @agent
    def job_discovery_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["job_discovery_agent"],  # type: ignore[index]
            tools=list(self._agent_tools.get("job_discovery_agent", ())),
        )

    @agent
    def job_enrichment_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["job_enrichment_agent"],  # type: ignore[index]
            tools=list(self._agent_tools.get("job_enrichment_agent", ())),
        )

    @task
    def discover_recommended_jobs(self) -> Task:
        return Task(
            config=self.tasks_config["discover_recommended_jobs"],  # type: ignore[index]
            agent=self.job_discovery_agent(),
        )

    @task
    def enrich_job_details(self) -> Task:
        return Task(
            config=self.tasks_config["enrich_job_details"],  # type: ignore[index]
            agent=self.job_enrichment_agent(),
            context=[self.discover_recommended_jobs()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.job_discovery_agent(),
                self.job_enrichment_agent(),
            ],
            tasks=[
                self.discover_recommended_jobs(),
                self.enrich_job_details(),
            ],
            process=Process.sequential,
            verbose=True,
        )


def get_linkedin_recommended_jobs_crew() -> Crew:
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = LinkedInRecommendedJobsCrew().crew()
    assert _cached_crew is not None
    return _cached_crew


def run_linkedin_recommended_jobs(
    *,
    profile_url: str,
    location: Optional[str] = None,
    keywords: Optional[str] = None,
    limit: int = 10,
    job_preferences: Optional[Dict[str, Any]] = None,
    tools_manager: Optional[MCPToolsManager] = None,
    write_outputs: bool = True,
    use_cached_crew: bool = True,
) -> Dict[str, Any]:
    crew_holder: Optional[LinkedInRecommendedJobsCrew] = None
    if tools_manager is not None:
        crew_holder = LinkedInRecommendedJobsCrew(tools_manager=tools_manager)
        crew_instance = crew_holder.crew()
    elif use_cached_crew:
        crew_instance = get_linkedin_recommended_jobs_crew()
    else:
        crew_holder = LinkedInRecommendedJobsCrew()
        crew_instance = crew_holder.crew()

    inputs = _filter_inputs(
        profile_url=profile_url,
        location=location,
        keywords=keywords,
        limit=limit,
        job_preferences=job_preferences,
    )
    try:
        raw_result = crew_instance.kickoff(inputs=inputs)
    finally:
        if crew_holder is not None and tools_manager is None:
            crew_holder.close()

    normalized = normalize_linkedin_recommended_jobs_output(raw_result)
    if write_outputs:
        write_recommended_job_outputs(normalized)
    return normalized


__all__ = [
    "LinkedInRecommendedJobsCrew",
    "get_linkedin_recommended_jobs_crew",
    "normalize_linkedin_recommended_jobs_output",
    "write_recommended_job_outputs",
    "run_linkedin_recommended_jobs",
]
