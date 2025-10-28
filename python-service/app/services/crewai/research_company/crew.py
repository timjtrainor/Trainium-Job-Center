import json
import logging
import os
from collections.abc import Mapping
from json import JSONDecodeError
from threading import Lock
from typing import Any, Dict, Optional

import yaml
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from crewai_tools import MCPServerAdapter

from ..mcp_config import get_mcp_server_config

_logger = logging.getLogger(__name__)

# MCP Server configuration for the Gateway
_MCP_SERVER_CONFIG = get_mcp_server_config()

_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

@CrewBase
class ResearchCompanyCrew:
    base_dir = os.path.dirname(__file__)
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    tools_config = os.path.join(base_dir, "config", "tools.yaml")

    def __init__(self):
        super().__init__()
        self._mcp_tools = None
        self._mcp_adapter = None

    def _get_mcp_tools(self):
        """Get MCP tools using MCPServerAdapter."""
        if self._mcp_tools is None:
            try:
                _logger.info(
                    "Connecting to MCP Gateway at %s with transport=%s",
                    _MCP_SERVER_CONFIG[0]["url"],
                    _MCP_SERVER_CONFIG[0]["transport"],
                )
                self._mcp_adapter = MCPServerAdapter(_MCP_SERVER_CONFIG)
                self._mcp_tools = self._mcp_adapter.__enter__()
                _logger.info(
                    "Available MCP Tools: %s",
                    [tool.name for tool in self._mcp_tools],
                )
            except Exception as e:
                _logger.error("Failed to connect to MCP Gateway: %s", e)
                self._mcp_tools = []
        return self._mcp_tools

    def _get_tools_for_agent(self, section: str):
        """Return a filtered set of tools for a specific agent section in tools.yaml."""
        all_tools = self._get_mcp_tools()
        try:
            with open(self.tools_config, "r") as f:
                tool_config = yaml.safe_load(f)
            allowed = {name.lower() for name in tool_config.get(section, [])}
        except Exception as e:
            _logger.error("Failed to load tools.yaml section '%s': %s", section, e)
            return []
        return [tool for tool in all_tools if tool.name.lower() in allowed]

    @agent
    def financial_analyst(self) -> Agent:
        tools = self._get_tools_for_agent("research_tools")
        _logger.info("Financial analyst tools injected: %s", [t.name for t in tools])
        return Agent(
            config=self.agents_config["financial_analyst"],  # type: ignore[index]
            tools=tools,
        )

    @agent
    def culture_investigator(self) -> Agent:
        tools = self._get_tools_for_agent("research_tools")
        _logger.info("Culture investigator tools injected: %s", [t.name for t in tools])
        return Agent(
            config=self.agents_config["culture_investigator"],  # type: ignore[index]
            tools=tools,
        )

    @agent
    def leadership_analyst(self) -> Agent:
        tools = self._get_tools_for_agent("research_tools")
        _logger.info("Leadership analyst tools injected: %s", [t.name for t in tools])
        return Agent(
            config=self.agents_config["leadership_analyst"],  # type: ignore[index]
            tools=tools,
        )

    @agent
    def career_growth_analyst(self) -> Agent:
        tools = self._get_tools_for_agent("research_tools")
        _logger.info("Career growth analyst tools injected: %s", [t.name for t in tools])
        return Agent(
            config=self.agents_config["career_growth_analyst"],  # type: ignore[index]
            tools=tools,
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
            agent=self.financial_analyst(),
            async_execution=True
        )

    @task
    def culture_investigation_task(self) -> Task:
        return Task(
            config=self.tasks_config["culture_investigation_task"],  # type: ignore[index]
            agent=self.culture_investigator(),
            async_execution=True
        )

    @task
    def leadership_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["leadership_analysis_task"],  # type: ignore[index]
            agent=self.leadership_analyst(),
            async_execution=True
        )

    @task
    def career_growth_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["career_growth_analysis_task"],  # type: ignore[index]
            agent=self.career_growth_analyst(),
            async_execution=True
        )

    @task
    def report_compilation_task(self) -> Task:
        return Task(
            config=self.tasks_config["report_compilation_task"],  # type: ignore[index]
            agent=self.report_writer(),
            async_execution=False
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.financial_analyst(),
                self.culture_investigator(),
                self.leadership_analyst(),
                self.career_growth_analyst(),
                self.report_writer()
            ],
            tasks=[
                self.financial_analysis_task(),
                self.culture_investigation_task(),
                self.leadership_analysis_task(),
                self.career_growth_analysis_task(),
                self.report_compilation_task()
            ],
            process=Process.sequential,
            verbose=True,
        )

    def close(self):
        """Explicitly cleanup MCP adapter."""
        if self._mcp_adapter:
            try:
                self._mcp_adapter.__exit__(None, None, None)
            except Exception as e:
                _logger.error("Error cleaning up MCP adapter: %s", e)

def get_research_company_crew() -> Crew:
    """Factory function to create a fresh crew instance per run."""
    return ResearchCompanyCrew().crew()
