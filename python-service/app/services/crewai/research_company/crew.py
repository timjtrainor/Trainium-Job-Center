from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

@CrewBase
class ResearchCompanyCrew:
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

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
    def latest_news_task(self) -> Task:
        return Task(
            config=self.tasks_config["latest_news_task"],  # type: ignore[index]
        )

    @task
    def financial_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["financial_analysis_task"],  # type: ignore[index]
        )

    @task
    def culture_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["culture_analysis_task"],  # type: ignore[index]
        )

    @task
    def leadership_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["leadership_analysis_task"],  # type: ignore[index]
        )

    @task
    def career_growth_task(self) -> Task:
        return Task(
            config=self.tasks_config["career_growth_task"],  # type: ignore[index]
        )

    @task
    def synthesis_task(self) -> Task:
        return Task(
            config=self.tasks_config["synthesis_task"],  # type: ignore[index]
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
            tasks=[self.research_strategy_task(), self.latest_news_task(), self.financial_analysis_task(), self.culture_analysis_task(), self.leadership_analysis_task(), self.career_growth_task(), self.synthesis_task(), self.final_report_task()],
            manager_agent=self.research_manager(),
            process=Process.sequential,
            verbose=True,
        )


def get_research_company_crew():
    return ResearchCompanyCrew().crew()