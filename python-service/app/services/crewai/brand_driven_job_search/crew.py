"""
Brand-Driven Job Search CrewAI implementation.

This crew performs autonomous job searches by deriving queries from career brand
data stored in ChromaDB and scoring results for brand alignment.
"""
from threading import Lock
from typing import Optional, Dict, Any
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from loguru import logger

from ..tools.chroma_search import get_career_brand_tools
from .brand_search import brand_search_helper

_cached_crew: Optional[Crew] = None
_crew_lock = Lock()


@CrewBase
class BrandDrivenJobSearchCrew:
    """
    Brand-Driven Job Search Crew for autonomous LinkedIn searches.
    
    This crew extracts career brand data from ChromaDB, generates targeted
    LinkedIn search queries based on brand dimensions, executes searches,
    and scores results for brand alignment.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize the crew and load required tools."""
        super().__init__()
        self._chroma_tools = None
        self._load_tools()

    def _load_tools(self):
        """Load ChromaDB tools."""
        try:
            # Career brand search tools for querying ChromaDB content
            self._chroma_tools = get_career_brand_tools()

            logger.info(f"Loaded {len(self._chroma_tools)} ChromaDB tools")

        except Exception as e:
            logger.warning(f"Failed to load tools: {e}")
            self._chroma_tools = []

    @agent
    def brand_query_generator(self) -> Agent:
        """Career brand query generator agent."""
        return Agent(
            config=self.agents_config["brand_query_generator"],
            tools=self._chroma_tools
        )

    @agent
    def linkedin_search_executor(self) -> Agent:
        """LinkedIn search execution specialist agent."""
        return Agent(
            config=self.agents_config["linkedin_search_executor"]
        )

    @agent
    def brand_alignment_scorer(self) -> Agent:
        """Brand-job alignment specialist agent."""
        return Agent(
            config=self.agents_config["brand_alignment_scorer"],
            tools=self._chroma_tools
        )

    @agent
    def orchestration_manager(self) -> Agent:
        """Brand-driven job search coordinator agent."""
        return Agent(
            config=self.agents_config["orchestration_manager"]
        )

    @task
    def generate_brand_queries_task(self) -> Task:
        """Generate LinkedIn search queries from career brand data."""
        return Task(
            config=self.tasks_config["generate_brand_queries_task"],
            agent=self.brand_query_generator(),
            async_execution=True
        )

    @task
    def execute_brand_searches_task(self) -> Task:
        """Execute LinkedIn searches using brand-derived queries."""
        return Task(
            config=self.tasks_config["execute_brand_searches_task"],
            agent=self.linkedin_search_executor(),
            context=[self.generate_brand_queries_task()],
            async_execution=True
        )

    @task
    def score_brand_alignment_task(self) -> Task:
        """Score job results for brand alignment."""
        return Task(
            config=self.tasks_config["score_brand_alignment_task"],
            agent=self.brand_alignment_scorer(),
            context=[self.generate_brand_queries_task(), self.execute_brand_searches_task()],
            async_execution=True
        )

    @task
    def compile_brand_driven_results_task(self) -> Task:
        """Compile final brand-driven job search results."""
        return Task(
            config=self.tasks_config["compile_brand_driven_results_task"],
            agent=self.orchestration_manager(),
            context=[
                self.generate_brand_queries_task(),
                self.execute_brand_searches_task(),
                self.score_brand_alignment_task()
            ]
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the brand-driven job search crew."""
        return Crew(
            agents=[
                self.brand_query_generator(),
                self.linkedin_search_executor(),
                self.brand_alignment_scorer(),
                self.orchestration_manager()
            ],
            tasks=[
                self.generate_brand_queries_task(),
                self.execute_brand_searches_task(),
                self.score_brand_alignment_task(),
                self.compile_brand_driven_results_task()
            ],
            process=Process.sequential,  # Tasks handle async execution internally
            verbose=True,
        )

    async def execute_brand_driven_search(self, user_id: str) -> Dict[str, Any]:
        """
        Execute brand-driven autonomous job search.
        
        Args:
            user_id: User ID for personalized brand data retrieval
            
        Returns:
            Dictionary containing brand-driven job search results
        """
        try:
            logger.info(f"Starting brand-driven job search for user: {user_id}")
            
            # First, try to generate search queries using the helper
            search_queries = await brand_search_helper.generate_search_queries(user_id)
            
            if not search_queries:
                logger.warning(f"No brand data found for user {user_id}")
                return {
                    "success": False,
                    "error": "No career brand data found",
                    "brand_driven_jobs": [],
                    "execution_summary": {
                        "total_jobs_found": 0,
                        "autonomous_search_success": False
                    }
                }
            
            # Execute the crew with user context
            result = self.crew().kickoff(inputs={"user_id": user_id})
            
            logger.info(f"Brand-driven job search completed for user: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Brand-driven job search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "brand_driven_jobs": [],
                "execution_summary": {
                    "total_jobs_found": 0,
                    "autonomous_search_success": False
                }
            }

    def get_brand_search_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get status of brand data availability for search generation.
        
        Args:
            user_id: User ID to check brand data for
            
        Returns:
            Dictionary containing brand data status
        """
        try:
            # This would be implemented to check ChromaDB for brand data
            # For now, return a basic status
            return {
                "user_id": user_id,
                "brand_data_available": True,  # Would check ChromaDB
                "brand_sections": brand_search_helper.BRAND_SECTIONS,
                "can_execute_search": True
            }
        except Exception as e:
            logger.error(f"Failed to get brand search status: {str(e)}")
            return {
                "user_id": user_id,
                "brand_data_available": False,
                "error": str(e),
                "can_execute_search": False
            }


def get_brand_driven_job_search_crew() -> BrandDrivenJobSearchCrew:
    """Factory function with singleton pattern for crew instances."""
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = BrandDrivenJobSearchCrew()
    assert _cached_crew is not None
    return _cached_crew


def run_brand_driven_job_search(user_id: str) -> Dict[str, Any]:
    """
    Convenience function to run brand-driven job search.
    
    Args:
        user_id: User ID for personalized brand-driven search
        
    Returns:
        Dictionary containing brand-aligned job search results
    """
    import asyncio
    
    crew = get_brand_driven_job_search_crew()
    
    # Handle async execution
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new one in a thread
            import concurrent.futures
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(crew.execute_brand_driven_search(user_id))
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=300)  # 5 minute timeout
        else:
            return loop.run_until_complete(crew.execute_brand_driven_search(user_id))
    except Exception as e:
        logger.error(f"Error running brand-driven search: {e}")
        return {
            "success": False,
            "error": str(e),
            "brand_driven_jobs": [],
            "execution_summary": {"autonomous_search_success": False}
        }