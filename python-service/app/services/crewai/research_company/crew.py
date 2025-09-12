from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from ..base import get_duckduckgo_tools

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
    def research_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["research_manager"],  # type: ignore[index]
        )

    @agent
    def financial_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_analyst"],  # type: ignore[index]
        )

    @agent
    def culture_investigator(self) -> Agent:
        return Agent(
            config=self.agents_config["culture_investigator"],  # type: ignore[index]
        )

    @agent
    def leadership_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["leadership_analyst"],  # type: ignore[index]
        )

    @agent
    def career_growth_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["career_growth_analyst"],  # type: ignore[index]
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
    def research_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_strategy_task"],  # type: ignore[index]
        )

    @task
    def final_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.research_manager(), self.financial_analyst(), self.culture_investigator(), self.leadership_analyst(), self.career_growth_analyst(), self.mcp_researcher(), self.report_writer()],
            tasks=[self.research_strategy_task(), self.final_report_task()],
            manager_agent=self.research_manager(),
            process=Process.sequential,
            verbose=True,
        )


def get_research_company_crew():
    return ResearchCompanyCrew().crew()
