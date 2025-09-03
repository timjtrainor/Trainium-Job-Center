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


class JobReviewCrew:
    """Crew configuration loading agents and tasks from YAML files."""
    _base_dir = Path(__file__).resolve().parent
    agents_config = str(_base_dir / "persona_catalog.yaml")
    tasks_config = str(_base_dir / "tasks.yaml")

    @crew
    def job_review(self) -> Crew:
        return Crew(
            agents=getattr(self, "agents", []),
            tasks=getattr(self, "tasks", []),
            process=Process.sequential,
        )


# Crew singleton
_job_review_crew: Optional[JobReviewCrew] = None


def get_job_review_crew() -> JobReviewCrew:
    """Get the singleton JobReviewCrew instance."""
    global _job_review_crew
    if _job_review_crew is None:
        _job_review_crew = JobReviewCrew()
    return _job_review_crew