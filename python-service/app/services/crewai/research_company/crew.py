from threading import Lock
from typing import Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from ..base import get_duckduckgo_tools


_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

@CrewBase
class ResearchCompanyCrew:
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    mcp_server_params = [
        {
            "url": "http://mcp-gateway:8811/sse",
            "transport": "sse"
        }
    ]

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_analyst"],  # type: ignore[index]
            tools=get_duckduckgo_tools()
        )

    @agent
    def culture_investigator(self) -> Agent:
        return Agent(
            config=self.agents_config["culture_investigator"],  # type: ignore[index]
            tools=get_duckduckgo_tools()
        )

    @agent
    def leadership_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["leadership_analyst"],  # type: ignore[index]
            tools=get_duckduckgo_tools()
        )

    @agent
    def career_growth_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["career_growth_analyst"],  # type: ignore[index]
            tools=get_duckduckgo_tools()
        )

    @agent
    def mcp_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["mcp_researcher"],  # type: ignore[index]
            tools=get_duckduckgo_tools()
        )

    @agent
    def report_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["report_writer"],  # type: ignore[index]
        )

    @task
    def financial_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["financial_analysis_task"],  # type: ignore[index]
            agent=self.financial_analyst()
        )

    @task
    def culture_investigation_task(self) -> Task:
        return Task(
            config=self.tasks_config["culture_investigation_task"],  # type: ignore[index]
            agent=self.culture_investigator()
        )

    @task
    def leadership_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["leadership_analysis_task"],  # type: ignore[index]
            agent=self.leadership_analyst()
        )

    @task
    def career_growth_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["career_growth_analysis_task"],  # type: ignore[index]
            agent=self.career_growth_analyst()
        )

    @task
    def web_research_task(self) -> Task:
        return Task(
            config=self.tasks_config["web_research_task"],  # type: ignore[index]
            agent=self.mcp_researcher()
        )

    @task
    def report_compilation_task(self) -> Task:
        return Task(
            config=self.tasks_config["report_compilation_task"],  # type: ignore[index]
            agent=self.report_writer()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.financial_analyst(),
                self.culture_investigator(),
                self.leadership_analyst(),
                self.career_growth_analyst(),
                self.mcp_researcher(),
                self.report_writer()
            ],
            tasks=[
                self.financial_analysis_task(),
                self.culture_investigation_task(),
                self.leadership_analysis_task(),
                self.career_growth_analysis_task(),
                self.web_research_task(),
                self.report_compilation_task()
            ],
            process=Process.sequential,
            verbose=True,
        )

def get_research_company_crew() -> Crew:
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = ResearchCompanyCrew().crew()
    assert _cached_crew is not None
    return _cached_crew