"""
LinkedIn Job Search CrewAI implementation.

This crew coordinates LinkedIn job searches and recommendations using LinkedIn MCP tools.
"""
from threading import Lock
from typing import Optional, Dict, Any

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew


_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

@CrewBase
class LinkedInJobSearchCrew:
    """
    LinkedIn Job Search crew for comprehensive LinkedIn job discovery and analysis.

    This crew follows the standard multi-agent pattern with specialist
    agents coordinated by a manager agent for final synthesis.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def linkedin_job_searcher(self) -> Agent:
        """Specialist agent for LinkedIn job search."""
        return Agent(
            config=self.agents_config["linkedin_job_searcher"],  # type: ignore[index]
        )

    @agent
    def job_opportunity_analyzer(self) -> Agent:
        """Specialist agent for analyzing LinkedIn job opportunities."""
        return Agent(
            config=self.agents_config["job_opportunity_analyzer"],  # type: ignore[index]
        )

    @agent
    def networking_strategist(self) -> Agent:
        """Specialist agent for LinkedIn networking strategies."""
        return Agent(
            config=self.agents_config["networking_strategist"],  # type: ignore[index]
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
    return crew.kickoff(inputs=inputs)