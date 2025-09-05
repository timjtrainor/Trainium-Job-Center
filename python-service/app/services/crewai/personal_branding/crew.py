"""
TODO: Comment this file
"""
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from loguru import logger

from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff
from crewai.llm import BaseLLM
from crewai.tools import tool

from .. import base
from ...llm_clients import LLMRouter
from ....core.config import get_settings
from ....models.jobspy import ScrapedJob
from app.services.crewai.tools.pg_search import pg_search


@CrewBase
class PersonalBrandCrew:
    """
    TODO: comment this class
    """
    
    def __init__(self):
        """Initialize the PersonalBrandCrew with YAML configurations."""
        self.base_dir = Path(__file__).resolve().parent.parent
        self.crew_name = "personal_brand"
        settings = get_settings()
        self._router = LLMRouter(preferences=settings.llm_preference)
        self._agent_llms: Dict[str, BaseLLM] = {}
        self.tasks_config = base.load_tasks_config(self.base_dir, "personal_branding/config")

    def _parse_model_config(self, models: List[Dict[str, Any]] | None) -> List[Tuple[str, str]]:
        """Convert agent model configs to provider/model tuples."""
        if not models:
            return []
        prefs: List[Tuple[str, str]] = []
        for entry in models:
            provider = entry.get("provider")
            model = entry.get("model")
            if not provider or not model:
                continue
            provider = provider.lower()
            if provider == "google":
                provider = "gemini"
            prefs.append((provider, model))
        return prefs

    class _RouterLLM(BaseLLM):
        """Adapter to use LLMRouter with CrewAI agents."""

        def __init__(self, router: LLMRouter, preferences: List[Tuple[str, str]] | None = None):
            model_name = preferences[0][1] if preferences else "router"
            super().__init__(model=model_name)
            self._router = router
            self._preferences = preferences or []

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

            if self._preferences:
                original = list(self._router.providers)
                try:
                    ordered = self._preferences + [p for p in original if p not in self._preferences]
                    self._router.providers = ordered
                    return self._router.generate(prompt)
                finally:
                    self._router.providers = original
            return self._router.generate(prompt)

    def _get_agent_llm(self, agent_name: str, config: Dict[str, Any]) -> BaseLLM:
        """Get or create RouterLLM for an agent."""
        if agent_name in self._agent_llms:
            return self._agent_llms[agent_name]
        prefs = self._parse_model_config(config.get("models"))
        llm = self._RouterLLM(self._router, prefs if prefs else None)
        self._agent_llms[agent_name] = llm
        return llm

    @tool
    def pg_search_tool(self) -> str:
        """Fetch strategic narratives from Postgres."""
        return pg_search(getattr(self, "_narrative_name", None))
        
    @agent
    def branding_agent(self) -> Agent:
        """
    Personal branding agent that reviews strategic narratives and
    creates branding documents.
        """
        config = self.agents_config["branding_agent"]

        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            tools=config.get("tools"),
            llm=self._get_agent_llm("branding_agent", config),
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 60),
            verbose=config.get("verbose", True)
        )

    @task
    def personal_branding_review(self) -> Task:
        """
    Task that pulls the 'Product Manager' strategic narrative
    and generates a personal branding document.
        """
        config = self.tasks_config["personal_branding_review"]
        agent_method = getattr(self, config["agent"])

        task = Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=agent_method(),
            async_execution=False,
            metadata=config.get("metadata", {}),
        )

        narrative_name = task.metadata.get("narrative_name") if task.metadata else None
        if narrative_name:
            self._narrative_name = narrative_name

        return task

    @crew
    def branding_crew(self) -> Crew:
        """Assemble the branding crew with one agent and one task."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )

# Crew singleton
_personal_brand_crew: Optional[PersonalBrandCrew] = None


def get_personal_brand_crew() -> PersonalBrandCrew:
    """
    Get the singleton PersonalBrandCrew instance.
    
    Returns:
        PersonalBrandCrew instance
    """
    global _personal_brand_crew
    if _personal_brand_crew is None:
        try:
            _personal_brand_crew = PersonalBrandCrew()
            logger.info("PersonalBrandCrew initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PersonalBrandCrew: {str(e)}")
            raise
    return _personal_brand_crew
