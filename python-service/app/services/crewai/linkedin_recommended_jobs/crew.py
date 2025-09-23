"""CrewAI implementation for LinkedIn recommended jobs."""

from __future__ import annotations

from threading import Lock
from typing import Any, Dict, Optional

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from loguru import logger

_CACHED_CREW: Optional[Crew] = None
_CREW_LOCK = Lock()


@CrewBase
class LinkedInRecommendedJobsCrew:
    """Crew orchestrating LinkedIn recommended job insights."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def recommendations_researcher(self) -> Agent:
        """Agent responsible for gathering LinkedIn recommendation signals."""

        return Agent(
            config=self.agents_config["recommendations_researcher"],
        )

    @agent
    def opportunity_synthesizer(self) -> Agent:
        """Agent that prioritizes and explains the recommended jobs."""

        return Agent(
            config=self.agents_config["opportunity_synthesizer"],
        )

    @task
    def analyze_recommendations_task(self) -> Task:
        """Task focused on aggregating LinkedIn recommendation sources."""

        return Task(
            config=self.tasks_config["analyze_recommendations_task"],
            agent=self.recommendations_researcher(),
            async_execution=True,
        )

    @task
    def summarize_recommendations_task(self) -> Task:
        """Task that produces the final recommendation set for the user."""

        return Task(
            config=self.tasks_config["summarize_recommendations_task"],
            agent=self.opportunity_synthesizer(),
            context=[self.analyze_recommendations_task()],
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the LinkedIn recommended jobs crew."""

        return Crew(
            agents=[
                self.recommendations_researcher(),
                self.opportunity_synthesizer(),
            ],
            tasks=[
                self.analyze_recommendations_task(),
                self.summarize_recommendations_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )


def get_linkedin_recommended_jobs_crew() -> Crew:
    """Return a cached LinkedIn recommended jobs crew instance."""

    global _CACHED_CREW

    if _CACHED_CREW is None:
        with _CREW_LOCK:
            if _CACHED_CREW is None:
                _CACHED_CREW = LinkedInRecommendedJobsCrew().crew()

    assert _CACHED_CREW is not None
    return _CACHED_CREW


def run_linkedin_recommended_jobs(
    inputs: Optional[Dict[str, Any]] = None,
    *,
    profile_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the LinkedIn recommended jobs crew with optional profile context."""

    payload: Dict[str, Any] = dict(inputs or {})

    if profile_url:
        payload["profile_url"] = profile_url
    else:
        payload.pop("profile_url", None)

    try:
        crew = get_linkedin_recommended_jobs_crew()
        return crew.kickoff(inputs=payload)
    except Exception as exc:
        logger.error("LinkedIn recommended jobs crew failed: {}", exc)
        return {
            "success": False,
            "error": str(exc),
            "recommended_jobs": [],
            "metadata": {"profile_url_provided": bool(profile_url)},
        }
