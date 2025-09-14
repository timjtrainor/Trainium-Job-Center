"""
JobReviewCrew - CrewAI multi-agent job analysis system.

This crew implements a comprehensive job review system using specialized agents
to analyze different aspects of job postings including skills, compensation, 
and quality assessment.
"""
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from loguru import logger

from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff
from crewai.llm import BaseLLM
from crewai.tools import BaseTool

from .. import base
from ...ai.llm_clients import LLMRouter
from ....core.config import get_settings
from ....schemas.jobspy import ScrapedJob


@CrewBase
class JobReviewCrew:
    """
    Multi-agent crew for comprehensive job posting analysis.
    
    Uses specialized agents to analyze:
    - Skills and requirements (researcher agent)
    - Compensation and benefits (negotiator agent) 
    - Quality and red flags (skeptic agent)
    """
    
    def __init__(self):
        """Initialize the JobReviewCrew with YAML configurations."""
        self.base_dir = Path(__file__).resolve().parent.parent
        self.crew_name = "job_review"
        settings = get_settings()
        self._router = LLMRouter(preferences=settings.llm_preference)
        self._agent_llms: Dict[str, BaseLLM] = {}
        self.tasks_config = base.load_tasks_config(self.base_dir, "job_review/config")

    def _load_tools(self, tool_names: List[str]) -> List[BaseTool]:
        """Resolve tool names to actual implementations using MCP Gateway.

        Loads tools from MCP servers through the Docker MCP Gateway.
        Falls back to empty list if MCP tools are unavailable.
        """
        if not tool_names:
            return []
            
        try:
            # Load tools from MCP Gateway
            mcp_tools = base.load_mcp_tools_sync(tool_names)
            if mcp_tools:
                logger.info(f"Loaded {len(mcp_tools)} MCP tools: {[t.name for t in mcp_tools]}")
                return mcp_tools
            else:
                logger.warning(f"No MCP tools loaded for: {tool_names}")
                return []
        except Exception as e:
            logger.error(f"Failed to load MCP tools: {e}")
            return []

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
        
    @agent
    def researcher_agent(self) -> Agent:
        """
        Create researcher agent for skills and requirements analysis.
        
        Returns:
            Agent configured for job skills analysis
        """
        config = base.load_agent_config(self.base_dir, "researcher")
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("researcher", config),
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 60),
            tools=self._load_tools(config.get("tools", [])),
            verbose=True
        )
    
    @agent
    def negotiator_agent(self) -> Agent:
        """
        Create negotiator agent for compensation analysis.
        
        Returns:
            Agent configured for compensation evaluation
        """
        config = base.load_agent_config(self.base_dir, "negotiator")
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("negotiator", config),
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 60),
            tools=self._load_tools(config.get("tools", [])),
            verbose=True
        )
    
    @agent
    def skeptic_agent(self) -> Agent:
        """
        Create skeptic agent for quality assessment and red flag detection.
        
        Returns:
            Agent configured for quality and risk assessment
        """
        config = base.load_agent_config(self.base_dir, "skeptic")
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("skeptic", config),
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 60),
            tools=self._load_tools(config.get("tools", [])),
            verbose=True
        )
    
    @task
    def skills_analysis_task(self) -> Task:
        """
        Create task for analyzing job skills and requirements.

        Returns:
            Task for skills analysis using researcher agent
        """
        config = self.tasks_config["skills_analysis"]
        agent_method = getattr(self, config["agent"])
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=agent_method(),
            async_execution=True
        )
    
    @task
    def compensation_analysis_task(self) -> Task:
        """
        Create task for analyzing compensation and benefits.

        Returns:
            Task for compensation analysis using negotiator agent
        """
        config = self.tasks_config["compensation_analysis"]
        agent_method = getattr(self, config["agent"])
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=agent_method(),
            async_execution=True
        )
    
    @task
    def quality_assessment_task(self) -> Task:
        """
        Create task for quality assessment and red flag detection.

        Returns:
            Task for quality assessment using skeptic agent
        """
        config = self.tasks_config["quality_assessment"]
        agent_method = getattr(self, config["agent"])
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=agent_method(),
            async_execution=True
        )
    
    @crew
    def job_review(self) -> Crew:
        """
        Assemble the job review crew with all agents and tasks.
        
        Returns:
            Configured crew for job analysis
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            memory=False  # Disable memory to avoid API key requirements
        )
    
    @before_kickoff
    def prepare_analysis(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare inputs before crew execution and inject MCP tools.
        
        Args:
            inputs: Raw inputs for the crew
            
        Returns:
            Processed inputs ready for analysis
        """
        logger.info("Preparing job analysis inputs and loading MCP tools")
        
        # Extract job data
        job_data = inputs.get("job", {})
        
        # Validate required fields
        required_fields = ["title", "company", "description"]
        missing_fields = [field for field in required_fields if not job_data.get(field)]
        
        if missing_fields:
            logger.warning(f"Missing job fields: {missing_fields}")
        
        # Load DuckDuckGo tools from MCP Gateway
        try:
            duckduckgo_tools = base.get_duckduckgo_tools()
            if duckduckgo_tools:
                logger.info(f"Loaded {len(duckduckgo_tools)} DuckDuckGo tools for agents")
                inputs["mcp_tools"] = duckduckgo_tools
            else:
                logger.warning("No DuckDuckGo tools available from MCP Gateway")
                inputs["mcp_tools"] = []
        except Exception as e:
            logger.error(f"Failed to load DuckDuckGo tools: {e}")
            inputs["mcp_tools"] = []
        
        # Add mock mode flag
        inputs["mock_mode"] = base.get_mock_mode()
        
        base.log_crew_execution(self.crew_name, inputs, "preparation_complete")
        return inputs
    
    @after_kickoff
    def finalize_analysis(self, output: Any) -> Any:
        """
        Process results after crew execution.
        
        Args:
            output: Raw crew output
            
        Returns:
            Finalized analysis results
        """
        logger.info("Finalizing job analysis results")
        
        if base.get_mock_mode():
            # Return mock data for testing
            return {
                "analysis_type": "job_review",
                "mock_mode": True,
                "summary": "Mock job analysis completed",
                "skills_analysis": {"required_skills": ["Python", "React"], "experience_level": "Mid-Level"},
                "compensation_analysis": {"salary_analysis": "Competitive range", "benefits": ["Health", "401k"]},
                "quality_assessment": {"quality_score": 85, "red_flags": [], "green_flags": ["Clear requirements"]}
            }
        
        base.log_crew_execution(self.crew_name, {}, output)
        return output


# Crew factory


def get_job_review_crew() -> JobReviewCrew:
    """Create a new JobReviewCrew instance."""
    try:
        crew = JobReviewCrew()
        logger.info("JobReviewCrew initialized successfully")
        return crew
    except Exception as e:
        logger.error(f"Failed to initialize JobReviewCrew: {str(e)}")
        raise
