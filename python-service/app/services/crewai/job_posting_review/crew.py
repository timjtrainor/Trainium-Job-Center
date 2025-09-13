from threading import Lock
from typing import Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

from ..tools.chroma_search import chroma_search

_cached_crew: Optional[Crew] = None
_crew_lock = Lock()


@CrewBase
class JobPostingReviewCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # === Specialists ===
    @agent
    def job_intake_agent(self) -> Agent:
        return Agent(config=self.agents_config["job_intake_agent"])  # type: ignore[index]

    @agent
    def pre_filter_agent(self) -> Agent:
        return Agent(config=self.agents_config["pre_filter_agent"])  # type: ignore[index]

    @agent
    def quick_fit_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["quick_fit_analyst"],  # type: ignore[index]
            tools=[chroma_search],
        )

    @agent
    def brand_framework_matcher(self) -> Agent:
        return Agent(
            config=self.agents_config["brand_framework_matcher"],  # type: ignore[index]
            tools=[chroma_search],
        )

    # === Manager ===
    @agent
    def managing_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["managing_agent"],  # type: ignore[index]
            allow_delegation=True,
        )

    # === Tasks ===
    @task
    def intake_task(self) -> Task:
        return Task(
            config=self.tasks_config["intake_task"],  # type: ignore[index]
            agent=self.job_intake_agent(),
        )

    @task
    def pre_filter_task(self) -> Task:
        return Task(
            config=self.tasks_config["pre_filter_task"],  # type: ignore[index]
            agent=self.pre_filter_agent(),
        )

    @task
    def quick_fit_task(self) -> Task:
        return Task(
            config=self.tasks_config["quick_fit_task"],  # type: ignore[index]
            agent=self.quick_fit_analyst(),
        )

    @task
    def brand_match_task(self) -> Task:
        return Task(
            config=self.tasks_config["brand_match_task"],  # type: ignore[index]
            agent=self.brand_framework_matcher(),
        )

    @task
    def orchestration_task(self) -> Task:
        """Manager controls the workflow: calls intake → pre-filter → quick-fit → brand match if needed."""
        return Task(
            config=self.tasks_config["orchestration_task"],  # type: ignore[index]
            agent=self.managing_agent(),
            async_execution=False,
        )

    # === Crew ===
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.job_intake_agent(),
                self.pre_filter_agent(),
                self.quick_fit_analyst(),
                self.brand_framework_matcher(),
                self.managing_agent(),
            ],
            tasks=[
                self.intake_task(),
                self.pre_filter_task(),
                self.quick_fit_task(),
                self.brand_match_task(),
                self.orchestration_task(),
            ],
            process=Process.hierarchical,  # 👈 manager runs the show
            verbose=True,
        )


def get_job_posting_review_crew() -> Crew:
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = JobPostingReviewCrew().crew()
    assert _cached_crew is not None
    return _cached_crew


if __name__ == "__main__":
    result = get_job_posting_review_crew().kickoff(inputs={
        "job_posting": "Senior Machine Learning Engineer at Acme Corp, salary $200k, remote eligible..."
    })

    print("\n=== FINAL DECISION ===")
    print(result)