"""
LinkedIn Job Search CrewAI implementation.

This crew coordinates LinkedIn job searches and recommendations using LinkedIn MCP tools.
"""
from threading import Lock
from typing import Optional, Dict, Any
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from loguru import logger

from ..base import load_mcp_tools_sync

_cached_crew: Optional[Crew] = None
_crew_lock = Lock()


@CrewBase
class LinkedInJobSearchCrew:
    """
    LinkedIn Job Search Crew for executing parameterized LinkedIn searches.
    
    This crew uses LinkedIn MCP tools to perform both search_jobs and 
    get_recommended_jobs operations, then consolidates and deduplicates
    the results for database persistence.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize the crew and load LinkedIn MCP tools."""
        super().__init__()
        self._linkedin_tools = None
        self._load_linkedin_tools()

    def _load_linkedin_tools(self):
        """Load LinkedIn MCP tools for agent use."""
        try:
            # Load LinkedIn-specific tools
            linkedin_tool_names = ["search_jobs", "get_recommended_jobs"]
            self._linkedin_tools = load_mcp_tools_sync(linkedin_tool_names)
            logger.info(f"Loaded {len(self._linkedin_tools)} LinkedIn MCP tools")
        except Exception as e:
            logger.warning(f"Failed to load LinkedIn MCP tools: {e}")
            self._linkedin_tools = []

    @agent
    def search_agent(self) -> Agent:
        """LinkedIn job search specialist agent."""
        return Agent(
            config=self.agents_config["search_agent"],
            tools=self._linkedin_tools
        )

    @agent
    def recommendation_agent(self) -> Agent:
        """LinkedIn recommendations specialist agent."""
        return Agent(
            config=self.agents_config["recommendation_agent"],
            tools=self._linkedin_tools
        )

    @agent
    def orchestration_agent(self) -> Agent:
        """Job search coordinator agent."""
        return Agent(
            config=self.agents_config["orchestration_agent"]
        )

    @task
    def search_jobs_task(self) -> Task:
        """Execute LinkedIn job search with user parameters."""
        return Task(
            config=self.tasks_config["search_jobs_task"],
            agent=self.search_agent(),
            async_execution=True
        )

    @task
    def get_recommendations_task(self) -> Task:
        """Retrieve LinkedIn job recommendations."""
        return Task(
            config=self.tasks_config["get_recommendations_task"],
            agent=self.recommendation_agent(),
            async_execution=True
        )

    @task
    def consolidate_results_task(self) -> Task:
        """Consolidate and deduplicate search and recommendation results."""
        return Task(
            config=self.tasks_config["consolidate_results_task"],
            agent=self.orchestration_agent(),
            context=[self.search_jobs_task(), self.get_recommendations_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the LinkedIn job search crew."""
        return Crew(
            agents=[
                self.search_agent(),
                self.recommendation_agent(),
                self.orchestration_agent()
            ],
            tasks=[
                self.search_jobs_task(),
                self.get_recommendations_task(),
                self.consolidate_results_task()
            ],
            process=Process.sequential,  # Tasks handle async execution internally
            verbose=True,
        )

    def execute_search(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LinkedIn job search with provided parameters.
        
        Args:
            search_params: Dictionary containing search parameters like keywords,
                         location, job_type, etc.
        
        Returns:
            Dictionary containing consolidated job search results
        """
        try:
            logger.info(f"Starting LinkedIn job search with params: {list(search_params.keys())}")
            
            # Execute the crew with search parameters
            result = self.crew().kickoff(inputs=search_params)
            
            logger.info("LinkedIn job search completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"LinkedIn job search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "consolidated_jobs": [],
                "total_jobs": 0
            }


def get_linkedin_job_search_crew() -> LinkedInJobSearchCrew:
    """Factory function with singleton pattern for crew instances."""
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = LinkedInJobSearchCrew()
    assert _cached_crew is not None
    return _cached_crew


def run_linkedin_job_search(
    keywords: str,
    location: str = None,
    job_type: str = None,
    date_posted: str = None,
    experience_level: str = None,
    remote: bool = False,
    limit: int = 25
) -> Dict[str, Any]:
    """
    Convenience function to run LinkedIn job search with parameters.
    
    Args:
        keywords: Job search keywords
        location: Job location
        job_type: Type of job (full-time, part-time, etc.)
        date_posted: Date filter (past-24h, past-week, etc.)
        experience_level: Experience level filter
        remote: Whether to search for remote jobs
        limit: Maximum number of results
    
    Returns:
        Dictionary containing search results
    """
    search_params = {
        "keywords": keywords,
        "location": location,
        "job_type": job_type,
        "date_posted": date_posted,
        "experience_level": experience_level,
        "remote": remote,
        "limit": limit
    }
    
    # Remove None values
    search_params = {k: v for k, v in search_params.items() if v is not None}
    
    crew = get_linkedin_job_search_crew()
    return crew.execute_search(search_params)