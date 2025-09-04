"""
JobReviewCrew - CrewAI multi-agent job analysis system.

This crew implements a comprehensive job review system using specialized agents
to analyze different aspects of job postings including skills, compensation, 
and quality assessment.
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger

from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff

from .. import base
from ....models.jobspy import ScrapedJob


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
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 60),
            tools=config.get("tools", []),
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
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 60),
            tools=config.get("tools", []),
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
            max_iter=config.get("max_iter", 2),
            max_execution_time=config.get("max_execution_time", 60),
            tools=config.get("tools", []),
            verbose=True
        )
    
    @task
    def skills_analysis_task(self) -> Task:
        """
        Create task for analyzing job skills and requirements.
        
        Returns:
            Task for skills analysis using researcher agent
        """
        tasks_config = base.load_tasks_config(self.base_dir, self.crew_name)
        task_config = tasks_config["tasks"]["skills_analysis"]
        
        return Task(
            description=task_config["description"],
            expected_output=task_config["expected_output"],
            agent=self.researcher_agent(),
            async_execution=task_config.get("async_execution", False)
        )
    
    @task
    def compensation_analysis_task(self) -> Task:
        """
        Create task for analyzing compensation and benefits.
        
        Returns:
            Task for compensation analysis using negotiator agent
        """
        tasks_config = base.load_tasks_config(self.base_dir, self.crew_name)
        task_config = tasks_config["tasks"]["compensation_analysis"]
        
        return Task(
            description=task_config["description"],
            expected_output=task_config["expected_output"],
            agent=self.negotiator_agent(),
            async_execution=task_config.get("async_execution", False)
        )
    
    @task
    def quality_assessment_task(self) -> Task:
        """
        Create task for quality assessment and red flag detection.
        
        Returns:
            Task for quality assessment using skeptic agent
        """
        tasks_config = base.load_tasks_config(self.base_dir, self.crew_name)
        task_config = tasks_config["tasks"]["quality_assessment"]
        
        return Task(
            description=task_config["description"],
            expected_output=task_config["expected_output"],
            agent=self.skeptic_agent(),
            async_execution=task_config.get("async_execution", False)
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
            process=Process.sequential,
            verbose=True,
            memory=True
        )
    
    @before_kickoff
    def prepare_analysis(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare inputs before crew execution.
        
        Args:
            inputs: Raw inputs for the crew
            
        Returns:
            Processed inputs ready for analysis
        """
        logger.info("Preparing job analysis inputs")
        
        # Extract job data
        job_data = inputs.get("job", {})
        
        # Validate required fields
        required_fields = ["title", "company", "description"]
        missing_fields = [field for field in required_fields if not job_data.get(field)]
        
        if missing_fields:
            logger.warning(f"Missing job fields: {missing_fields}")
        
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


# Crew singleton
_job_review_crew: Optional[JobReviewCrew] = None


def get_job_review_crew() -> JobReviewCrew:
    """
    Get the singleton JobReviewCrew instance.
    
    Returns:
        JobReviewCrew instance
    """
    global _job_review_crew
    if _job_review_crew is None:
        try:
            _job_review_crew = JobReviewCrew()
            logger.info("JobReviewCrew initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize JobReviewCrew: {str(e)}")
            raise
    return _job_review_crew