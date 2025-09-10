"""
Job Posting Review Crew - YAML-driven CrewAI pipeline for motivational evaluator fan-out.

This module implements the motivational evaluator fan-out system using entirely
YAML-defined agents and tasks. Five motivational personas (builder, maximizer, 
harmonizer, pathfinder, adventurer) provide thumbs-up/thumbs-down verdicts.
"""

import uuid
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger

from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff
from crewai.llm import BaseLLM

from .. import base
from ...ai.llm_clients import LLMRouter
from ....core.config import get_settings


@CrewBase
class MotivationalFanOutCrew:
    """
    YAML-driven crew for motivational evaluator fan-out analysis.
    
    Uses five specialized motivational personas:
    - Builder: Technical building and systems design opportunities
    - Maximizer: Growth, compensation and value optimization  
    - Harmonizer: Culture and team dynamics alignment
    - Pathfinder: Strategic career path navigation
    - Adventurer: Innovation and learning exploration
    """
    
    def __init__(self):
        """Initialize the MotivationalFanOutCrew with YAML configurations."""
        self.base_dir = Path(__file__).resolve().parent
        self.crew_name = "motivational_fanout"
        settings = get_settings()
        self._router = LLMRouter(preferences=settings.llm_preference)
        self._agent_llms: Dict[str, BaseLLM] = {}
        self.agents_config = self._load_agents_config()
        self.tasks_config = self._load_tasks_config()

    def _load_agents_config(self) -> Dict[str, Any]:
        """Load agents configuration from YAML file."""
        config_file = self.base_dir / "config" / "agents.yaml"
        if not config_file.exists():
            raise FileNotFoundError(f"Agents configuration not found: {config_file}")
        
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.debug(f"Loaded agents config with {len(config)} agents")
            return config
        except Exception as e:
            logger.error(f"Failed to load agents config {config_file}: {str(e)}")
            raise

    def _load_tasks_config(self) -> Dict[str, Any]:
        """Load tasks configuration from YAML file."""
        config_file = self.base_dir / "config" / "tasks.yaml"
        if not config_file.exists():
            raise FileNotFoundError(f"Tasks configuration not found: {config_file}")
        
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.debug(f"Loaded tasks config with {len(config)} tasks")
            return config
        except Exception as e:
            logger.error(f"Failed to load tasks config {config_file}: {str(e)}")
            raise

    def _load_tools(self, tool_names: List[str]) -> List[Any]:
        """Resolve tool names to actual implementations."""
        if tool_names:
            logger.warning(f"Ignoring unsupported tools: {tool_names}")
        return []

    def _get_agent_llm(self, agent_name: str, config: Dict[str, Any]) -> BaseLLM:
        """Get or create RouterLLM for an agent."""
        if agent_name in self._agent_llms:
            return self._agent_llms[agent_name]
        
        # Use the same RouterLLM adapter from JobReviewCrew
        class _RouterLLM(BaseLLM):
            def __init__(self, router: LLMRouter, preferences: Optional[List] = None):
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
                return self._router.generate(prompt)
        
        llm = _RouterLLM(self._router)
        self._agent_llms[agent_name] = llm
        return llm
    
    @agent
    def builder_agent(self) -> Agent:
        """Evaluate career growth and trajectory potential"""
        config = self.agents_config["builder"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("builder", config),
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 45),
            tools=self._load_tools(config.get("tools", [])),
            verbose=True
        )

    @agent
    def maximizer_agent(self) -> Agent:
        """Evaluate compensation and rewards"""
        config = self.agents_config["maximizer"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("maximizer", config),
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 45),
            tools=self._load_tools(config.get("tools", [])),
            verbose=True
        )

    @agent
    def harmonizer_agent(self) -> Agent:
        """Evaluate culture and team alignment"""
        config = self.agents_config["harmonizer"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("harmonizer", config),
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 45),
            tools=self._load_tools(config.get("tools", [])),
            verbose=True
        )

    @agent
    def pathfinder_agent(self) -> Agent:
        """Evaluate lifestyle and flexibility fit"""
        config = self.agents_config["pathfinder"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("pathfinder", config),
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 45),
            tools=self._load_tools(config.get("tools", [])),
            verbose=True
        )

    @agent
    def adventurer_agent(self) -> Agent:
        """Evaluate purpose and impact alignment"""
        config = self.agents_config["adventurer"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("adventurer", config),
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 45),
            tools=self._load_tools(config.get("tools", [])),
            verbose=True
        )

    # Helper agents for advisory analysis
    @agent
    def data_analyst(self) -> Agent:
        """Create data analyst helper agent for compensation and market analysis."""
        config = self.agents_config["data_analyst"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("data_analyst", config),
            max_iter=config.get("max_iter", 1),
            max_execution_time=config.get("max_execution_time", 30),
            tools=self._load_tools(config.get("tools", [])),
            verbose=False  # Keep helper output minimal
        )

    @agent
    def strategist(self) -> Agent:
        """Create strategist helper agent for trend analysis."""
        config = self.agents_config["strategist"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("strategist", config),
            max_iter=config.get("max_iter", 1),
            max_execution_time=config.get("max_execution_time", 30),
            tools=self._load_tools(config.get("tools", [])),
            verbose=False
        )

    # The following helper agents are currently unused and can be removed or commented out
    # @agent
    # def stakeholder(self) -> Agent:
    #     """Create stakeholder helper agent for partnership analysis."""
    #     config = self.agents_config["stakeholder"]
    #     return Agent(
    #         role=config["role"],
    #         goal=config["goal"],
    #         backstory=config["backstory"],
    #         llm=self._get_agent_llm("stakeholder", config),
    #         max_iter=config.get("max_iter", 1),
    #         max_execution_time=config.get("max_execution_time", 30),
    #         tools=self._load_tools(config.get("tools", [])),
    #         verbose=False
    #     )
    #
    # @agent
    # def technical_leader(self) -> Agent:
    #     """Create technical leader helper agent for delivery analysis."""
    #     config = self.agents_config["technical_leader"]
    #     return Agent(
    #         role=config["role"],
    #         goal=config["goal"],
    #         backstory=config["backstory"],
    #         llm=self._get_agent_llm("technical_leader", config),
    #         max_iter=config.get("max_iter", 1),
    #         max_execution_time=config.get("max_execution_time", 30),
    #         tools=self._load_tools(config.get("tools", [])),
    #         verbose=False
    #     )
    #
    # @agent
    # def recruiter(self) -> Agent:
    #     """Create recruiter helper agent for ATS analysis."""
    #     config = self.agents_config["recruiter"]
    #     return Agent(
    #         role=config["role"],
    #         goal=config["goal"],
    #         backstory=config["backstory"],
    #         llm=self._get_agent_llm("recruiter", config),
    #         max_iter=config.get("max_iter", 1),
    #         max_execution_time=config.get("max_execution_time", 30),
    #         tools=self._load_tools(config.get("tools", [])),
    #         verbose=False
    #     )
    @agent
    def skeptic(self) -> Agent:
        """Create skeptic helper agent for risk analysis."""
        config = self.agents_config["skeptic"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self._get_agent_llm("skeptic", config),
            max_iter=config.get("max_iter", 1),
            max_execution_time=config.get("max_execution_time", 30),
            tools=self._load_tools(config.get("tools", [])),
            verbose=False
        )
    # @agent
    # def optimizer(self) -> Agent:
    #     """Create optimizer helper agent for application enhancement."""
    #     config = self.agents_config["optimizer"]
    #     return Agent(
    #         role=config["role"],
    #         goal=config["goal"],
    #         backstory=config["backstory"],
    #         llm=self._get_agent_llm("optimizer", config),
    #         max_iter=config.get("max_iter", 1),
    #         max_execution_time=config.get("max_execution_time", 30),
    #         tools=self._load_tools(config.get("tools", [])),
    #         verbose=False
    #     )

    @task
    def builder_evaluation_task(self) -> Task:
        """Create task for builder evaluation."""
        config = self.tasks_config["builder_evaluation"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.builder_agent(),
            async_execution=True  # Enable parallel execution
        )

    @task
    def maximizer_evaluation_task(self) -> Task:
        """Create task for maximizer evaluation."""
        config = self.tasks_config["maximizer_evaluation"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.maximizer_agent(),
            async_execution=True  # Enable parallel execution
        )

    @task
    def harmonizer_evaluation_task(self) -> Task:
        """Create task for harmonizer evaluation."""
        config = self.tasks_config["harmonizer_evaluation"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.harmonizer_agent(),
            async_execution=True  # Enable parallel execution
        )

    @task
    def pathfinder_evaluation_task(self) -> Task:
        """Create task for pathfinder evaluation."""
        config = self.tasks_config["pathfinder_evaluation"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.pathfinder_agent(),
            async_execution=True  # Enable parallel execution
        )

    @task
    def adventurer_evaluation_task(self) -> Task:
        """Create task for adventurer evaluation."""
        config = self.tasks_config["adventurer_evaluation"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.adventurer_agent(),
            async_execution=True  # Enable parallel execution
        )

    # Helper tasks for advisory analysis
    @task
    def data_analyst_task(self) -> Task:
        """Create task for data analyst helper."""
        config = self.tasks_config["data_analyst_task"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.data_analyst(),
            async_execution=False  # Sequential execution for helpers
        )

    @task
    def strategist_task(self) -> Task:
        """Create task for strategist helper."""
        config = self.tasks_config["strategist_task"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.strategist(),
            async_execution=False
        )

    # @task
    # def stakeholder_task(self) -> Task:
    #     """Create task for stakeholder helper."""
    #     config = self.tasks_config["stakeholder_task"]
    #     return Task(
    #         description=config["description"],
    #         expected_output=config["expected_output"],
    #         agent=self.stakeholder(),
    #         async_execution=False
    #     )
    #
    # @task
    # def technical_leader_task(self) -> Task:
    #     """Create task for technical leader helper."""
    #     config = self.tasks_config["technical_leader_task"]
    #     return Task(
    #         description=config["description"],
    #         expected_output=config["expected_output"],
    #         agent=self.technical_leader(),
    #         async_execution=False
    #     )
    #
    # @task
    # def recruiter_task(self) -> Task:
    #     """Create task for recruiter helper."""
    #     config = self.tasks_config["recruiter_task"]
    #     return Task(
    #         description=config["description"],
    #         expected_output=config["expected_output"],
    #         agent=self.recruiter(),
    #         async_execution=False
    #     )

    @task
    def skeptic_task(self) -> Task:
        """Create task for skeptic helper."""
        config = self.tasks_config["skeptic_task"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.skeptic(),
            async_execution=False
        )

    # @task
    # def optimizer_task(self) -> Task:
    #     """Create task for optimizer helper."""
    #     config = self.tasks_config["optimizer_task"]
    #     return Task(
    #         description=config["description"],
    #         expected_output=config["expected_output"],
    #         agent=self.optimizer(),
    #         async_execution=False
    #     )

    @task
    def helper_snapshot(self) -> Task:
        """Create task for helper snapshot aggregation."""
        config = self.tasks_config["helper_snapshot"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.data_analyst(),  # Use data_analyst agent for aggregation
            async_execution=False
        )

    @crew
    def motivational_fanout(self) -> Crew:
        """
        Assemble the motivational fan-out crew with all agents and tasks.

        Returns:
            Configured crew for motivational evaluator analysis
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Tasks will run in sequence but are designed for parallel evaluation
            verbose=True,
            memory=False  # Disable memory to avoid API key requirements
        )

    @before_kickoff
    def prepare_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare inputs before crew execution.

        Args:
            inputs: Raw inputs for the crew

        Returns:
            Processed inputs ready for analysis with proper placeholders
        """
        logger.info("Preparing motivational fan-out inputs with helper support")

        # Extract and normalize job posting data
        job_data = inputs.get("job_posting_data", inputs.get("job", {}))

        # Prepare standardized inputs that match YAML placeholders
        prepared_inputs = {
            "job_title": job_data.get("title", ""),
            "job_company": job_data.get("company", ""),
            "job_location": job_data.get("location", ""),
            "job_description": job_data.get("description", ""),
            "options": inputs.get("options", {}),
            "helper_snapshot": "{}"  # Initialize empty, will be populated by helper_snapshot task
        }

        # Validate required fields
        required_fields = ["job_title", "job_company", "job_description"]
        missing_fields = [field for field in required_fields if not prepared_inputs.get(field)]

        if missing_fields:
            logger.warning(f"Missing job fields: {missing_fields}")

        # Add mock mode flag
        prepared_inputs["mock_mode"] = base.get_mock_mode()

        base.log_crew_execution(self.crew_name, prepared_inputs, "preparation_complete")
        return prepared_inputs

    @after_kickoff
    def process_verdicts(self, output: Any) -> Dict[str, Any]:
        """
        Process results after crew execution.

        Args:
            output: Raw crew output

        Returns:
            Processed motivational verdicts ready for judge aggregation
        """
        logger.info("Processing motivational fan-out results with helper support")

        if base.get_mock_mode():
            # Return mock motivational verdicts for testing
            result = self._get_mock_verdicts_with_helpers()
            if not output.get("options", {}).get("use_helpers"):
                result["helper_snapshot"] = {}
            return result

        # Process actual crew results
        motivational_verdicts = []
        helper_snapshot = {}

        try:
            # Parse task outputs and extract JSON verdicts
            task_outputs = self._extract_task_outputs(output)

            # Extract helper snapshot if available
            helper_output = task_outputs.get("helper_snapshot", "")
            if helper_output:
                try:
                    helper_snapshot = self._parse_helper_snapshot(helper_output)
                except Exception as e:
                    logger.warning(f"Failed to parse helper snapshot: {str(e)}")
                    helper_snapshot = {}

            # Process motivational verdicts
            for persona_id in ["builder", "maximizer", "harmonizer", "pathfinder", "adventurer"]:
                try:
                    verdict = self._parse_verdict(task_outputs.get(f"{persona_id}_evaluation", ""), persona_id)
                    motivational_verdicts.append(verdict)
                except Exception as e:
                    logger.warning(f"Failed to parse {persona_id} verdict: {str(e)}")
                    # Add fallback verdict for failed tasks
                    motivational_verdicts.append({
                        "id": persona_id,
                        "recommend": False,
                        "reason": "insufficient signal",
                        "notes": ["task execution failed"],
                        "sources": ["error_handler"]
                    })

        except Exception as e:
            logger.error(f"Failed to process motivational verdicts: {str(e)}")
            # Return fallback verdicts for all personas
            for persona_id in ["builder", "maximizer", "harmonizer", "pathfinder", "adventurer"]:
                motivational_verdicts.append({
                    "id": persona_id,
                    "recommend": False,
                    "reason": "insufficient signal",
                    "notes": ["processing error"],
                    "sources": ["error_handler"]
                })

        result = {
            "motivational_verdicts": motivational_verdicts,
            "helper_snapshot": helper_snapshot
        }
        # Ensure verdicts use 'id' key
        for verdict in result["motivational_verdicts"]:
            if "persona_id" in verdict:
                verdict["id"] = verdict.pop("persona_id")
        base.log_crew_execution(self.crew_name, {}, result)
        return result

    def _get_mock_verdicts_with_helpers(self) -> Dict[str, Any]:
        """Return mock verdicts with helper insights for testing."""
        return {
            "motivational_verdicts": [
                {
                    "id": "builder",
                    "recommend": True,
                    "reason": "Strong career growth trajectory and leadership potential",
                    "notes": ["Complex system architecture", "Engineering ownership"],
                    "sources": ["job_description", "agent_knowledge", "helper_snapshot"]
                },
                {
                    "id": "maximizer",
                    "recommend": True,
                    "reason": "Competitive compensation and benefits package",
                    "notes": ["Market-rate salary", "Learning opportunities"],
                    "sources": ["job_description", "agent_knowledge", "helper_snapshot"]
                },
                {
                    "id": "harmonizer",
                    "recommend": True,
                    "reason": "Positive cultural alignment indicators",
                    "notes": ["Inclusive environment", "Work-life balance"],
                    "sources": ["job_description", "agent_knowledge", "helper_snapshot"]
                },
                {
                    "id": "pathfinder",
                    "recommend": True,
                    "reason": "Good flexibility and lifestyle balance",
                    "notes": ["Career progression path", "Industry growth"],
                    "sources": ["job_description", "agent_knowledge", "helper_snapshot"]
                },
                {
                    "id": "adventurer",
                    "recommend": True,
                    "reason": "Clear mission and meaningful impact",
                    "notes": ["Cutting-edge tech", "Learning challenges"],
                    "sources": ["job_description", "agent_knowledge", "helper_snapshot"]
                }
            ],
            "helper_snapshot": {
                "data_analyst": {"tc_range": "$120k-$160k", "refs": ["levels.fyi", "glassdoor"]},
                "strategist": {"signals": ["AI adoption", "cloud migration"], "refs": ["industry_report"]},
                "skeptic": {"redflags": []},
                "optimizer": {"top3": ["highlight cloud experience", "emphasize AI projects", "mention team leadership"]}
            }
        }
    
    def _parse_helper_snapshot(self, helper_output: str) -> Dict[str, Any]:
        """Parse helper snapshot JSON from task output."""
        try:
            # Try to extract JSON from helper output
            import re
            json_match = re.search(r'\{.*\}', helper_output, re.DOTALL)
            if json_match:
                helper_data = json.loads(json_match.group())
                
                # Validate it's a reasonable helper snapshot
                if isinstance(helper_data, dict):
                    # Limit size to prevent token bloat
                    serialized = json.dumps(helper_data)
                    if len(serialized) <= 1536:  # ~1.5KB limit
                        return helper_data
                    else:
                        logger.warning(f"Helper snapshot too large ({len(serialized)} chars), truncating")
                        # Return truncated version with key helpers only
                        return {
                            k: v for k, v in helper_data.items() 
                            if k in ["data_analyst", "skeptic", "optimizer"]
                        }
            
            # Fallback to empty if parsing fails
            return {}
            
        except Exception as e:
            logger.warning(f"Failed to parse helper snapshot JSON: {str(e)}")
            return {}
    
    def _extract_task_outputs(self, output: Any) -> Dict[str, str]:
        """Extract individual task outputs from crew result."""
        task_outputs = {}
        
        # Handle different output formats
        if hasattr(output, 'tasks_output'):
            for task_output in output.tasks_output:
                if hasattr(task_output, 'description') and hasattr(task_output, 'raw'):
                    # Extract task type from task description
                    description = str(task_output.description)
                    
                    # Check for helper_snapshot task
                    if "helper_snapshot" in description.lower() or "aggregate helper" in description.lower():
                        task_outputs["helper_snapshot"] = str(task_output.raw)
                    else:
                        # Check for motivational evaluation tasks
                        for persona in ["builder", "maximizer", "harmonizer", "pathfinder", "adventurer"]:
                            if persona in description.lower():
                                task_outputs[f"{persona}_evaluation"] = str(task_output.raw)
                                break
        elif isinstance(output, dict):
            # Handle dictionary output
            task_outputs = output
        elif isinstance(output, str):
            # Handle string output - assume it's from the last task
            task_outputs["combined_output"] = output
        
        return task_outputs
    
    def _parse_verdict(self, task_output: str, persona_id: str) -> Dict[str, Any]:
        """Parse JSON verdict from task output."""
        try:
            # Try to extract JSON from task output
            import re
            json_match = re.search(r'\{[^{}]*"persona_id"[^{}]*\}', task_output, re.DOTALL)
            if json_match:
                verdict_json = json.loads(json_match.group())
                # Validate required fields
                if all(key in verdict_json for key in ["persona_id", "recommend", "reason"]):
                    verdict_json["id"] = verdict_json.pop("persona_id")
                    return verdict_json
            
            # Fallback parsing if JSON structure is not found
            recommend = "recommend" in task_output.lower() and "true" in task_output.lower()
            reason_match = re.search(r'"reason":\s*"([^"]+)"', task_output)
            reason = reason_match.group(1) if reason_match else "Analysis completed"
            
            return {
                "id": persona_id,
                "recommend": recommend,
                "reason": reason,
                "notes": ["parsed from text output"],
                "sources": ["task_analysis"]
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse JSON verdict for {persona_id}: {str(e)}")
            raise


# Updated run_crew function to use the new MotivationalFanOutCrew
def run_crew(
    job_posting_data: Dict[str, Any], 
    options: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute the YAML-defined motivational fan-out crew.
    
    This function serves as the main entry point for the HTTP route,
    executing the five motivational evaluators in a fan-out pattern.
    
    Args:
        job_posting_data: Job posting data to analyze
        options: Optional configuration parameters
        correlation_id: Request correlation ID for tracking
        
    Returns:
        FitReviewResult-compatible dictionary with motivational verdicts
        
    Raises:
        Exception: If crew execution fails
    """
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
        
    logger.info(
        f"Starting motivational fan-out crew execution",
        extra={
            "correlation_id": correlation_id,
            "job_title": job_posting_data.get("title"),
            "job_company": job_posting_data.get("company")
        }
    )
    
    try:
        # Initialize the YAML-driven motivational crew
        crew_instance = MotivationalFanOutCrew()
        crew = crew_instance.motivational_fanout()
        
        # Prepare inputs for the crew
        inputs = {
            "job_posting_data": job_posting_data,
            "options": options or {},
        }
        
        # Execute the crew with the job data
        result = crew.kickoff(inputs=inputs)
        
        # Transform result to match FitReviewResult schema
        formatted_result = _format_crew_result(result, job_posting_data, correlation_id)
        
        logger.info(
            f"Motivational fan-out crew execution completed successfully",
            extra={
                "correlation_id": correlation_id,
                "verdicts_count": len(formatted_result.get("motivational_verdicts", []))
            }
        )
        
        return formatted_result
        
    except Exception as e:
        logger.error(
            f"Motivational fan-out crew execution failed: {str(e)}",
            extra={"correlation_id": correlation_id}
        )
        raise


def _format_crew_result(
    crew_result: Any, 
    job_posting_data: Dict[str, Any], 
    correlation_id: str
) -> Dict[str, Any]:
    """
    Format crew execution result to match FitReviewResult schema.
    
    Args:
        crew_result: Raw result from crew execution
        job_posting_data: Original job posting data
        correlation_id: Request correlation ID
        
    Returns:
        Formatted result matching FitReviewResult schema
    """
    # Generate job_id from URL or use correlation_id
    job_url = job_posting_data.get("url", "")
    job_id = f"job_{hash(job_url)}" if job_url else correlation_id
    
    # Handle motivational verdicts from the new crew
    if isinstance(crew_result, dict) and "motivational_verdicts" in crew_result:
        verdicts = [
            {**v, "id": v.pop("persona_id")} if "persona_id" in v else v
            for v in crew_result["motivational_verdicts"]
        ]
        
        # Aggregate recommendations
        total_verdicts = len(verdicts)
        positive_verdicts = sum(1 for v in verdicts if v.get("recommend", False))
        recommendation_ratio = positive_verdicts / total_verdicts if total_verdicts > 0 else 0
        
        # Determine overall recommendation
        overall_recommend = recommendation_ratio >= 0.6  # Majority rule with 60% threshold
        confidence = "high" if recommendation_ratio >= 0.8 or recommendation_ratio <= 0.2 else "medium"
        
        # Generate rationale
        if overall_recommend:
            rationale = f"Positive alignment across {positive_verdicts}/{total_verdicts} motivational evaluators"
        else:
            rationale = f"Mixed signals with only {positive_verdicts}/{total_verdicts} positive evaluations"
        
        return {
            "job_id": job_id,
            "final": {
                "recommend": overall_recommend,
                "rationale": rationale,
                "confidence": confidence
            },
            "personas": verdicts,  # Use motivational verdicts as personas
            "motivational_verdicts": verdicts,  # Also include for judge aggregation
            "tradeoffs": [
                "Technical complexity vs learning curve",
                "Growth potential vs current compensation",
                "Cultural fit vs career advancement"
            ],
            "actions": [
                "Deep dive into technical requirements",
                "Research company culture and values", 
                "Evaluate long-term career trajectory"
            ],
            "sources": list(set([
                source for verdict in verdicts 
                for source in verdict.get("sources", [])
            ]))
        }
    
    # Handle mock mode results
    if isinstance(crew_result, dict) and crew_result.get("mock_mode"):
        return {
            "job_id": job_id,
            "final": {
                "recommend": True,
                "rationale": "Mock analysis shows positive fit based on YAML-defined motivational criteria",
                "confidence": "high"
            },
            "personas": [
                {
                    "id": "builder",
                    "recommend": True,
                    "reason": "Strong technical building opportunities",
                    "notes": ["Modern tech stack", "System design challenges"],
                    "sources": ["job_description", "technical_requirements"]
                },
                {
                    "id": "maximizer",
                    "recommend": True,
                    "reason": "Excellent growth and optimization potential",
                    "notes": ["Market-rate compensation", "Career advancement"],
                    "sources": ["compensation_analysis", "growth_opportunities"]
                },
                {
                    "id": "harmonizer",
                    "recommend": True,
                    "reason": "Positive cultural alignment indicators",
                    "notes": ["Collaborative environment", "Work-life balance"],
                    "sources": ["culture_indicators", "work_environment"]
                },
                {
                    "id": "pathfinder",
                    "recommend": True,
                    "reason": "Strategic career path alignment",
                    "notes": ["Industry positioning", "Skill development"],
                    "sources": ["career_strategy", "industry_analysis"]
                },
                {
                    "id": "adventurer",
                    "recommend": True,
                    "reason": "Innovation and learning opportunities",
                    "notes": ["Emerging technologies", "Creative challenges"],
                    "sources": ["innovation_indicators", "learning_opportunities"]
                }
            ],
            "tradeoffs": [
                "Innovation pace vs stability",
                "Learning curve vs immediate impact",
                "Remote flexibility vs team collaboration"
            ],
            "actions": [
                "Research company innovation culture",
                "Evaluate technical learning opportunities",
                "Assess career growth trajectory"
            ],
            "sources": [
                "job_description",
                "company_research", 
                "industry_analysis",
                "career_insights"
            ]
        }
    
    # Attempt to parse unexpected crew results and surface errors
    try:
        parsed_result = (
            json.loads(crew_result) if isinstance(crew_result, str) else crew_result
        )
    except Exception as parse_err:
        logger.error(
            "Malformed crew result: JSON parsing failed",
            extra={
                "correlation_id": correlation_id,
                "raw_result": str(crew_result)[:1000],
                "error": str(parse_err)
            }
        )
        raise ValueError("Failed to parse crew result") from parse_err

    if isinstance(parsed_result, dict) and "motivational_verdicts" in parsed_result:
        return _format_crew_result(parsed_result, job_posting_data, correlation_id)

    logger.error(
        "Malformed crew result: missing 'motivational_verdicts'",
        extra={
            "correlation_id": correlation_id,
            "raw_result": str(parsed_result)[:1000]
        }
    )
    raise ValueError("Crew result missing 'motivational_verdicts'")
