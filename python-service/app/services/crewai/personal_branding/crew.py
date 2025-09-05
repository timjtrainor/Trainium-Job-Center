from typing import Dict, List, Any, Optional, Tuple
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
import logging


logger = logging.getLogger(__name__)


@CrewBase
class PersonalBrandCrew:
    """LatestAiDevelopment crew for personal branding"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @before_kickoff
    def prepare_inputs(self, inputs):
        # Modify inputs before the crew starts
        inputs["additional_data"] = "Some extra information"
        return inputs

    @after_kickoff
    def process_output(self, output):
        # Modify output after the crew finishes
        output.raw += "\nProcessed after kickoff."
        return output

    @agent
    def branding_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["branding_agent"],  # type: ignore[index]
            verbose=True,
        )

    @task
    def personal_branding_review(self) -> Task:
        return Task(
            config=self.tasks_config["personal_branding_review"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,  # Automatically collected by the @agent decorator
            tasks=self.tasks,    # Automatically collected by the @task decorator.
            process=Process.sequential,
            verbose=True,
        )


_personal_brand_crew: Optional[PersonalBrandCrew] = None


def get_personal_brand_crew() -> PersonalBrandCrew:
    """Get a singleton instance of PersonalBrandCrew."""
    global _personal_brand_crew
    if _personal_brand_crew is None:
        try:
            _personal_brand_crew = PersonalBrandCrew()
            logger.info("PersonalBrandCrew initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PersonalBrandCrew: {str(e)}")
            raise
    return _personal_brand_crew

