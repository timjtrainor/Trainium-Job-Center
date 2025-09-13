"""
Job Posting Review Crew - Multi-agent job posting fit evaluation.

This crew evaluates job postings against the user's career brand framework
by analyzing skills fit, culture alignment, compensation competitiveness, 
and overall career trajectory match using company research data.
"""

from threading import Lock
from typing import Optional
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

from ..base import get_duckduckgo_tools
from ..tools.chroma_search import ChromaSearchTool


_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

@CrewBase
class JobPostingReviewCrew:
    """
    Job posting fit evaluation crew that analyzes opportunities against 
    career brand framework using company research data.
    
    This crew follows the standard multi-agent pattern with specialist
    agents coordinated by a manager agent for final synthesis.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def skills_analyst(self) -> Agent:
        """Specialist agent for analyzing skills and requirements fit."""
        return Agent(
            config=self.agents_config["skills_analyst"],  # type: ignore[index]
            tools=[ChromaSearchTool(collection_name="career_brand", n_results=3)]
        )

    @agent
    def culture_analyst(self) -> Agent:
        """Specialist agent for analyzing cultural fit and alignment."""
        return Agent(
            config=self.agents_config["culture_analyst"],  # type: ignore[index]
            tools=[ChromaSearchTool(collection_name="career_brand", n_results=3)]
        )

    @agent
    def compensation_analyst(self) -> Agent:
        """Specialist agent for analyzing compensation competitiveness."""
        return Agent(
            config=self.agents_config["compensation_analyst"],  # type: ignore[index]
            tools=get_duckduckgo_tools()
        )

    @agent
    def career_trajectory_analyst(self) -> Agent:
        """Specialist agent for analyzing career growth potential."""
        return Agent(
            config=self.agents_config["career_trajectory_analyst"],  # type: ignore[index]
            tools=[ChromaSearchTool(collection_name="career_brand", n_results=3)]
        )

    @agent
    def fit_evaluator(self) -> Agent:
        """Manager agent that synthesizes all analyses into fit evaluation."""
        return Agent(
            config=self.agents_config["fit_evaluator"],  # type: ignore[index]
        )

    @task
    def skills_analysis_task(self) -> Task:
        """Analyze skills requirements and candidate fit."""
        return Task(
            config=self.tasks_config["skills_analysis_task"],  # type: ignore[index]
            agent=self.skills_analyst(),
            async_execution=True
        )

    @task
    def culture_analysis_task(self) -> Task:
        """Analyze cultural fit and company alignment."""
        return Task(
            config=self.tasks_config["culture_analysis_task"],  # type: ignore[index]
            agent=self.culture_analyst(),
            async_execution=True
        )

    @task
    def compensation_analysis_task(self) -> Task:
        """Analyze compensation competitiveness and benefits."""
        return Task(
            config=self.tasks_config["compensation_analysis_task"],  # type: ignore[index]
            agent=self.compensation_analyst(),
            async_execution=True
        )

    @task
    def career_trajectory_analysis_task(self) -> Task:
        """Analyze career growth and trajectory potential."""
        return Task(
            config=self.tasks_config["career_trajectory_analysis_task"],  # type: ignore[index]
            agent=self.career_trajectory_analyst(),
            async_execution=True
        )

    @task
    def fit_evaluation_task(self) -> Task:
        """Synthesize all analyses into final fit evaluation."""
        return Task(
            config=self.tasks_config["fit_evaluation_task"],  # type: ignore[index]
            agent=self.fit_evaluator(),
            context=[
                self.skills_analysis_task(),
                self.culture_analysis_task(),
                self.compensation_analysis_task(),
                self.career_trajectory_analysis_task()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the complete job posting review crew."""
        return Crew(
            agents=[
                self.skills_analyst(),
                self.culture_analyst(),
                self.compensation_analyst(),
                self.career_trajectory_analyst(),
                self.fit_evaluator()
            ],
            tasks=[
                self.skills_analysis_task(),
                self.culture_analysis_task(),
                self.compensation_analysis_task(),
                self.career_trajectory_analysis_task(),
                self.fit_evaluation_task()
            ],
            process=Process.hierarchical,
            manager_agent=self.fit_evaluator(),
            verbose=True,
        )


def get_job_posting_review_crew() -> Crew:
    """Factory function with singleton pattern for crew instances."""
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = JobPostingReviewCrew().crew()
    assert _cached_crew is not None
    return _cached_crew
