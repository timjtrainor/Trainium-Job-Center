from threading import Lock
from typing import Optional, Dict, Any

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew


_cached_crew: Optional[Crew] = None
_crew_lock = Lock()


@CrewBase
class LinkedinJobSearchCrew:
    """
    LinkedIn Job Search Crew for searching and processing job listings from LinkedIn.
    
    This crew uses LinkedIn search tools to find job opportunities based on user criteria
    and processes the results into structured data suitable for database persistence.
    
    The crew follows a sequential process:
    1. LinkedIn Job Searcher - Searches LinkedIn for matching jobs
    2. Job Processor - Structures and validates the search results
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    mcp_server_params = [
        {
            "url": "http://mcp-gateway:8811/sse",
            "transport": "sse"
        }
    ]

    @agent
    def linkedin_job_searcher(self) -> Agent:
        """LinkedIn search specialist agent with access to LinkedIn tools."""
        return Agent(
            config=self.agents_config["linkedin_job_searcher"],  # type: ignore[index]
        )

    @agent
    def job_processor(self) -> Agent:
        """Job data processing specialist for structuring search results."""
        return Agent(
            config=self.agents_config["job_processor"],  # type: ignore[index]
        )

    @task
    def linkedin_search_task(self) -> Task:
        """Task to search LinkedIn for job listings based on criteria."""
        return Task(
            config=self.tasks_config["linkedin_search_task"],  # type: ignore[index]
            agent=self.linkedin_job_searcher(),
        )

    @task
    def job_processing_task(self) -> Task:
        """Task to process and structure the LinkedIn search results."""
        return Task(
            config=self.tasks_config["job_processing_task"],  # type: ignore[index]
            agent=self.job_processor(),
            context=[self.linkedin_search_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the LinkedIn job search crew."""
        return Crew(
            agents=[
                self.linkedin_job_searcher(),
                self.job_processor()
            ],
            tasks=[
                self.linkedin_search_task(),
                self.job_processing_task()
            ],
            process=Process.sequential,
            verbose=True,
        )


def get_linkedin_job_search_crew() -> Crew:
    """Factory function with singleton pattern for LinkedIn job search crew instances."""
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = LinkedinJobSearchCrew().crew()
    assert _cached_crew is not None
    return _cached_crew


def run_linkedin_job_search(search_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute LinkedIn job search with the provided parameters.
    
    Args:
        search_params: Search parameters including job_title, location, etc.
        
    Returns:
        Processed job search results ready for database persistence
    """
    crew = get_linkedin_job_search_crew()
    
    # Execute the crew with search parameters
    result = crew.kickoff(inputs=search_params)
    
    # The result should be from the job_processing_task which returns structured data
    if hasattr(result, 'raw'):
        return result.raw
    else:
        return result