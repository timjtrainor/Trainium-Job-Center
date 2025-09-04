"""
CrewAI-inspired job review service for multi-agent job analysis.

This service implements a multi-agent approach to job review, where different
specialized "agents" analyze various aspects of job postings to provide
comprehensive insights and recommendations.
"""
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from loguru import logger
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff

from ..models.jobspy import ScrapedJob
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .evaluation_pipeline import Task


class JobReviewCrew(CrewBase):
    """Crew configuration loading agents and tasks from YAML files."""
    _base_dir = Path(__file__).resolve().parent
    agents_config = str(_base_dir / "crewai_agents")
    tasks_config = str(_base_dir / "crewai_tasks")

    @agent
    def researcher_agent(self) -> Agent:
        """Create researcher agent from YAML configuration."""
        return Agent(
            config=self.agents_config,
            name="researcher",
            verbose=True
        )

    @agent  
    def negotiator_agent(self) -> Agent:
        """Create negotiator agent from YAML configuration."""
        return Agent(
            config=self.agents_config,
            name="negotiator",
            verbose=True
        )

    @agent
    def skeptic_agent(self) -> Agent:
        """Create skeptic agent from YAML configuration."""
        return Agent(
            config=self.agents_config,
            name="skeptic",
            verbose=True
        )

    @task
    def skills_analysis_task(self) -> Task:
        """Create skills analysis task from YAML configuration."""
        return Task(
            config=self.tasks_config,
            name="skills_analysis",
            agent=self.researcher_agent()
        )

    @task
    def compensation_analysis_task(self) -> Task:
        """Create compensation analysis task from YAML configuration."""
        return Task(
            config=self.tasks_config,
            name="compensation_analysis",
            agent=self.negotiator_agent()
        )

    @task
    def quality_assessment_task(self) -> Task:
        """Create quality assessment task from YAML configuration."""
        return Task(
            config=self.tasks_config,
            name="quality_assessment",
            agent=self.skeptic_agent()
        )

    @crew
    def job_review(self) -> Crew:
        """Assemble the job review crew with YAML-configured agents and tasks."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )


# Crew singleton
_job_review_crew: Optional[JobReviewCrew] = None


def get_job_review_crew() -> JobReviewCrew:
    """Get the singleton JobReviewCrew instance."""
    global _job_review_crew
    if _job_review_crew is None:
        _job_review_crew = JobReviewCrew()
    return _job_review_crew
