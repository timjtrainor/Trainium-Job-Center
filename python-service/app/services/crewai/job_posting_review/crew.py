"""Clean CrewAI agent and task definitions for job posting review. Business logic in YAML configs."""

import os
from threading import Lock
from typing import Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

from ..knowledge_sources import get_knowledge_sources_from_config

# Set environment variables to minimize CrewAI logging and event issues
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("CREWAI_DISABLE_EVENTS", "true")



_cached_crew: Optional[Crew] = None
_crew_lock = Lock()


@CrewBase
class JobPostingReviewCrew:
    """Clean CrewAI configuration with business logic in YAML files and tools."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def _create_agent_with_knowledge_sources(self, agent_config: dict) -> Agent:
        """Create an agent and replace knowledge sources with concrete implementations."""
        # Remove knowledge_sources from config to prevent abstract class instantiation
        config_copy = agent_config.copy()
        knowledge_sources_config = config_copy.pop('knowledge_sources', None)

        # Create agent without knowledge sources
        agent = Agent(config=config_copy)

        # Add concrete knowledge sources if they were specified
        if knowledge_sources_config:
            concrete_sources = get_knowledge_sources_from_config(knowledge_sources_config)
            if concrete_sources:
                # Add knowledge sources to the agent
                agent.knowledge_sources = concrete_sources

        return agent

    @agent
    def pre_filter_agent(self) -> Agent:
        """Agent that applies hard-coded rejection rules to filter unqualified jobs."""
        return Agent(config=self.agents_config["pre_filter_agent"])  # type: ignore[index]

    @agent
    def north_star_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's North Star & Vision."""
        return self._create_agent_with_knowledge_sources(self.agents_config["north_star_matcher"])  # type: ignore[index]

    @agent
    def trajectory_mastery_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Trajectory & Mastery goals."""
        return self._create_agent_with_knowledge_sources(self.agents_config["trajectory_mastery_matcher"])  # type: ignore[index]

    @agent
    def values_compass_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Values Compass."""
        return self._create_agent_with_knowledge_sources(self.agents_config["values_compass_matcher"])  # type: ignore[index]

    @agent
    def lifestyle_alignment_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Lifestyle preferences."""
        return self._create_agent_with_knowledge_sources(self.agents_config["lifestyle_alignment_matcher"])  # type: ignore[index]

    @agent
    def compensation_philosophy_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Compensation Philosophy."""
        return self._create_agent_with_knowledge_sources(self.agents_config["compensation_philosophy_matcher"])  # type: ignore[index]

    @agent
    def purpose_impact_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Purpose & Impact goals."""
        return self._create_agent_with_knowledge_sources(self.agents_config["purpose_impact_matcher"])  # type: ignore[index]

    @agent
    def industry_focus_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Industry Focus preferences."""
        return self._create_agent_with_knowledge_sources(self.agents_config["industry_focus_matcher"])  # type: ignore[index]

    @agent
    def company_filters_matcher(self) -> Agent:
        """Agent that evaluates job alignment with user's Company culture preferences."""
        return self._create_agent_with_knowledge_sources(self.agents_config["company_filters_matcher"])  # type: ignore[index]

    @agent
    def constraints_matcher(self) -> Agent:
        """Agent that evaluates job compliance with user's hard requirements and deal-breakers."""
        return self._create_agent_with_knowledge_sources(self.agents_config["constraints_matcher"])  # type: ignore[index]

    @agent
    def brand_match_manager(self) -> Agent:
        """Manager agent that synthesizes brand dimension specialist results."""
        return Agent(config=self.agents_config["brand_match_manager"])  # type: ignore[index]

    @task
    def pre_filter_task(self):
        """Task to evaluate basic job qualifications with rule-based filtering."""
        return Task(
            config=self.tasks_config["pre_filter_task"],  # type: ignore[index]
            agent=self.pre_filter_agent(),
        )

    @task
    def north_star_task(self):
        """Task to analyze job alignment with North Star & Vision."""
        return Task(
            config=self.tasks_config["north_star_task"],  # type: ignore[index]
            agent=self.north_star_matcher(),
            async_execution=True,
        )

    @task
    def trajectory_mastery_task(self):
        """Task to analyze job alignment with Trajectory & Mastery."""
        return Task(
            config=self.tasks_config["trajectory_mastery_task"],  # type: ignore[index]
            agent=self.trajectory_mastery_matcher(),
            async_execution=True,
        )

    @task
    def values_compass_task(self):
        """Task to analyze job alignment with Values Compass."""
        return Task(
            config=self.tasks_config["values_compass_task"],  # type: ignore[index]
            agent=self.values_compass_matcher(),
            async_execution=True,
        )

    @task
    def lifestyle_alignment_task(self):
        """Task to analyze job alignment with Lifestyle preferences."""
        return Task(
            config=self.tasks_config["lifestyle_alignment_task"],  # type: ignore[index]
            agent=self.lifestyle_alignment_matcher(),
            async_execution=True,
        )

    @task
    def compensation_philosophy_task(self):
        """Task to analyze job alignment with Compensation Philosophy."""
        return Task(
            config=self.tasks_config["compensation_philosophy_task"],  # type: ignore[index]
            agent=self.compensation_philosophy_matcher(),
            async_execution=True,
        )

    @task
    def purpose_impact_task(self):
        """Task to analyze job alignment with Purpose & Impact."""
        return Task(
            config=self.tasks_config["purpose_impact_task"],  # type: ignore[index]
            agent=self.purpose_impact_matcher(),
            async_execution=True,
        )

    @task
    def industry_focus_task(self):
        """Task to analyze job alignment with Industry Focus."""
        return Task(
            config=self.tasks_config["industry_focus_task"],  # type: ignore[index]
            agent=self.industry_focus_matcher(),
            async_execution=True,
        )

    @task
    def company_filters_task(self):
        """Task to analyze job alignment with Company Filters."""
        return Task(
            config=self.tasks_config["company_filters_task"],  # type: ignore[index]
            agent=self.company_filters_matcher(),
            async_execution=True,
        )

    @task
    def constraints_task(self):
        """Task to analyze job compliance with Constraints."""
        return Task(
            config=self.tasks_config["constraints_task"],  # type: ignore[index]
            agent=self.constraints_matcher(),
            async_execution=True,
        )

    @task
    def brand_match_task(self):
        """Task to synthesize all brand dimension analyses into final recommendation."""
        return Task(
            config=self.tasks_config["brand_match_task"],  # type: ignore[index]
            agent=self.brand_match_manager(),
            context=[
                self.north_star_task(),
                self.trajectory_mastery_task(),
                self.values_compass_task(),
                self.lifestyle_alignment_task(),
                self.compensation_philosophy_task(),
                self.purpose_impact_task(),
                self.industry_focus_task(),
                self.company_filters_task(),
                self.constraints_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        """Crew definition focused on agent/task configuration."""
        return Crew(
            agents=[
                self.pre_filter_agent(),
                # All 9 parallel brand dimension specialists
                self.north_star_matcher(),
                self.trajectory_mastery_matcher(),
                self.values_compass_matcher(),
                self.lifestyle_alignment_matcher(),
                self.compensation_philosophy_matcher(),
                self.purpose_impact_matcher(),
                self.industry_focus_matcher(),
                self.company_filters_matcher(),
                self.constraints_matcher(),
                # Manager that synthesizes results
                self.brand_match_manager(),
            ],
            tasks=[
                self.pre_filter_task(),
                # All brand analysis tasks run in parallel
                self.north_star_task(),
                self.trajectory_mastery_task(),
                self.values_compass_task(),
                self.lifestyle_alignment_task(),
                self.compensation_philosophy_task(),
                self.purpose_impact_task(),
                self.industry_focus_task(),
                self.company_filters_task(),
                self.constraints_task(),
                # Final synthesis task
                self.brand_match_task(),
            ],
            process=Process.sequential,  # Orchestration handled externally
            verbose=True,
        )


def get_job_posting_review_crew() -> Crew:
    """Get cached CrewAI crew instance."""
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = JobPostingReviewCrew().crew()
    return _cached_crew


def run_crew(job_posting_data: dict, options: dict = None, correlation_id: str = None) -> dict:
    """
    Execute the job posting review crew.

    Note: This function now delegates orchestration to the JobPostingOrchestrator
    for better separation of concerns. Direct crew execution is not recommended.
    """
    from .orchestrator import evaluate_job_posting
    return evaluate_job_posting(job_posting_data, correlation_id)


# For backward compatibility and testing
if __name__ == "__main__":
    from .orchestrator import evaluate_job_posting

    sample = {
        "title": "Senior Machine Learning Engineer",
        "company": "Acme Corp",
        "description": "Build ML systems",
        "highest_salary": 250000,
        "seniority": "Senior",
        "job_type": "remote"
    }

    result = evaluate_job_posting(sample)
    print("Job Evaluation Result:")
    print(f"Final Recommendation: {result.get('final', {}).get('recommend', 'Unknown')}")
    print(f"Confidence: {result.get('final', {}).get('confidence', 'Unknown')}")
    print(f"Rationale: {result.get('final', {}).get('rationale', 'No rationale provided')}")
