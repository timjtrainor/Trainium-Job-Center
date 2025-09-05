"""CrewAI configuration for personal brand job review."""
from typing import Dict, Any

from crewai import Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew

from .pg_search import get_pg_search_tool


class PersonalBrandCrew(CrewBase):
    """Crew for reviewing job postings with Postgres search capability."""

    agents_config = {
        "researcher": {
            "role": "Database Researcher",
            "goal": "Find similar job postings in the database",
            "backstory": "Uses PostgREST to search the jobs table",
            "tools": ["pg_search_tool"],
            "verbose": True,
        }
    }

    tools = {"pg_search_tool": get_pg_search_tool}

    @task
    def search_database(self) -> Task:
        async def _run(job: Dict[str, Any]):
            query = job.get("title", "")
            tool = get_pg_search_tool()
            return await tool.search_jobs(query)

        return Task(
            description="Search stored jobs for similar titles",
            expected_output="List of matching jobs",
            agent="researcher",
            coroutine=_run,
        )

    @crew
    def personal_brand(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential)

