from typing import Dict, List, Any, Optional, Tuple
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai.llm import BaseLLM
import logging

from ...ai.llm_clients import LLMRouter
from ....core.config import get_settings

from ..tools import get_postgres_tool


logger = logging.getLogger(__name__)


@CrewBase
class PersonalBrandCrew:
    """LatestAiDevelopment crew for personal branding"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self):
        """Initialize the PersonalBrandCrew with LLM router."""
        settings = get_settings()
        self._router = LLMRouter(preferences=settings.llm_preference)

    class _RouterLLM(BaseLLM):
        """Adapter to use LLMRouter with CrewAI agents."""

        def __init__(self, router: LLMRouter):
            super().__init__(model="gpt-oss:20b")
            self._router = router

        def call(
            self,
            messages: Any,
            tools: Optional[List[dict]] = None,
            callbacks: Optional[List[Any]] = None,
            available_functions: Optional[Dict[str, Any]] = None,
            from_task: Optional[Any] = None,
            from_agent: Optional[Any] = None,
        ) -> str:
            if isinstance(messages, list):
                prompt = "\n".join(m.get("content", "") for m in messages if isinstance(m, dict))
            else:
                prompt = str(messages)
            return self._router.generate(prompt)

    @before_kickoff
    def prepare_inputs(self, inputs):
        # Modify inputs before the crew starts
        query = """
        SELECT
        --    sn.narrative_id
        --    , sn.user_id
        --    , sn.narrative_name
              u.first_name 
            , u.last_name
            , sn.desired_title
            , sn.positioning_statement
            , sn.signature_capability
            , sn.impact_story_title
            , sn.impact_story_body
        --    ,sn.default_resume_id
        --    ,sn.created_at
        --    ,sn.updated_at
            , sn.desired_industry
            , sn.desired_company_stage
            , sn.mission_alignment
            , sn.long_term_legacy
            , sn.key_strengths
            , sn.representative_metrics
            , sn.leadership_style
            , sn.communication_style
            , sn.working_preferences
            , sn.preferred_locations
        --    , sn.relocation_open,
            , sn.compensation_expectation
            , sn.impact_stories
        FROM
            strategic_narratives sn
        JOIN
            users u 
            ON
            sn.user_id = u.user_id 
        WHERE
            sn.narrative_name = 'Product Manager'
        """
        try:
            tool = get_postgres_tool()
            db_results = tool(query)
            inputs["additional_data"] = db_results
        except Exception as e:
            inputs["additional_data"] = f"Failed to fetch data from database: {str(e)}"
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
            llm=self._RouterLLM(self._router)
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
            process=Process.hierarchical,
            verbose=True,
        )


def get_personal_brand_crew() -> PersonalBrandCrew:
    """Create a new PersonalBrandCrew instance."""
    try:
        crew = PersonalBrandCrew()
        logger.info("PersonalBrandCrew initialized successfully")
        return crew
    except Exception as e:
        logger.error(f"Failed to initialize PersonalBrandCrew: {str(e)}")
        raise

