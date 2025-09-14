# AGENT.md - CrewAI Multi-Crew Architecture Guide

## Introduction

This document provides comprehensive guidance for AI agents and developers working with CrewAI crews in the Trainium Job Center project. It establishes coding standards, architectural patterns, and maintenance requirements to ensure consistent implementation of multi-agent systems.

**Purpose**: This guide enables AI agents to write structured, maintainable CrewAI code by following established patterns from our active implementations (`job_posting_review`, `personal_branding`, and `research_company` crews). It ensures consistency across all crew implementations and provides clear standards for YAML configurations, task delegation, and FastAPI integration.

**Critical Requirement**: This AGENT.md file MUST be updated whenever any changes are made to crew structures, YAML configurations, FastAPI endpoints, or CrewAI implementation patterns.

## File Structure Overview

All CrewAI crews follow a standardized directory structure based on the scalable multi-crew pattern:

```
app/services/crewai/
├── base.py                           # Shared CrewBase utilities and tools
├── agents/                           # Shared agent YAML configurations (optional)
├── tools/                           # Shared tool definitions
│   ├── __init__.py
│   ├── chroma_search.py
│   └── custom_pg.py
├── job_posting_review/              # Job posting review crew
│   ├── __init__.py
│   ├── crew.py                      # JobPostingReviewCrew class
│   └── config/                      # Crew-specific configurations
│       ├── agents.yaml              # Agent definitions for job posting review
│       └── tasks.yaml               # Task definitions for job posting review
├── personal_branding/               # Personal branding crew
│   ├── __init__.py
│   ├── crew.py                      # PersonalBrandCrew class
│   └── config/                      # Crew-specific configurations
│       ├── agents.yaml              # Agent definitions for personal branding
│       └── tasks.yaml               # Task definitions for personal branding
└── research_company/                # Company research crew
    ├── __init__.py
    ├── crew.py                      # ResearchCompanyCrew class
    └── config/
        ├── agents.yaml              # Company research agents
        └── tasks.yaml               # Company research tasks
```

### Required Files for Each Crew

1. **`crew.py`** - Main crew class using CrewAI decorators
2. **`config/agents.yaml`** - Agent definitions with roles, goals, and configurations
3. **`config/tasks.yaml`** - Task definitions with descriptions and expected outputs
4. **`__init__.py`** - Module initialization and crew factory function

## Agent Definitions

### YAML Configuration Structure

All agents must be defined in the `config/agents.yaml` file following this structure:

```yaml
# Standard CrewAI Fields (used directly by CrewAI framework)
agent_name:
  role: "Agent Role Title"                    # CrewAI agent role
  goal: "Clear objective for this agent"      # CrewAI agent goal
  backstory: >                               # CrewAI agent backstory
    Detailed background explaining the agent's expertise,
    experience, and perspective. Should be written in second
    person ("You are...") and include tool access information.
  llm: "openai/gpt-5-mini"                   # LLM model specification
  temperature: 0.2                           # Model temperature (0.0-1.0)
  memory: false                              # Enable/disable agent memory
  max_iter: 1                                # Maximum iterations
  verbose: true                              # Enable verbose logging
  allow_delegation: false                    # Allow task delegation to other agents
  mcp_tools:                                 # MCP tool names
    - duckduckgo
    - web_search
  constraints:                               # Optional behavioral constraints
    - "Write in a clear, candidate-friendly tone"
    - "Do not add unsupported claims"
    - "Format output for readability"

# For agents using shared configurations, reference the shared agent:
shared_agent_name:
  # Reference to shared agent in /agents/ directory
  extends: "researcher"  # References /agents/researcher.yaml
  # Override specific fields if needed
  temperature: 0.3
```

### Agent Configuration Guidelines

1. **Role**: Should be descriptive and specific to the agent's function
2. **Goal**: Must be clear, actionable, and measurable
3. **Backstory**: Written in second person, explains expertise and tool access
4. **Temperature**: 
   - `0.1-0.3` for analytical/factual tasks
   - `0.4-0.6` for creative/synthesis tasks
   - `0.7+` for highly creative tasks
5. **Tools**: Use MCP tools for external integrations, shared tools for internal operations

### Shared Agent Pattern

Leverage shared agents from `/agents/` directory for common roles:

```python
@agent
def researcher(self) -> Agent:
    """Load shared researcher agent configuration."""
    config = load_agent_config(Path(__file__).parent.parent, "researcher")
    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        max_iter=config.get("max_iter", 2),
        max_execution_time=config.get("max_execution_time", 30),
        tools=get_shared_tools(config.get("tools", []))
    )
```

## Task Definitions

### YAML Configuration Structure

All tasks must be defined in the `config/tasks.yaml` file:

```yaml
task_name:
  description: >
    Detailed description of what the task should accomplish.
    Use {{variable_name}} for dynamic inputs that will be provided
    at execution time. Be specific about research requirements,
    data sources, and analysis depth.
    
  expected_output: >
    Precisely define the expected output format, typically as JSON.
    Include all required fields, data types, and structure.
    Example:
    A JSON object with analysis results:
    {
      "analysis_category": {
        "field1": "description of field1",
        "field2": "description of field2",
        "score": "numeric score 1-100",
        "insights": ["array of key insights"]
      }
    }
  
  agent: agent_name                          # Agent responsible for this task
  context: [prerequisite_task_names]         # Tasks that must complete first
  async_execution: true                      # Enable parallel execution
```

### Task Configuration Guidelines

1. **Description**: Use dynamic variables ({{company_name}}) for flexibility
2. **Expected Output**: Embed a concise JSON schema using `model_json_schema()` so required
   fields are explicit; field names must match the schema exactly.
3. **Context Dependencies**: List prerequisite tasks that provide necessary data
4. **Async Execution**: Enable for tasks that can run in parallel

### Task Dependency Patterns

```yaml
# Sequential execution (each task depends on previous)
web_research_task:
  description: "Gather initial company information..."
  agent: mcp_researcher

analysis_task:
  description: "Analyze the research data..."
  agent: analyst
  context: [web_research_task]

compilation_task:
  description: "Compile final report..."
  agent: report_writer
  context: [web_research_task, analysis_task]
```

## Task Delegation and Manager Agents

### Manager Agent Pattern

Use a manager agent to coordinate multiple specialist agents and compile results:

```python
@agent
def report_writer(self) -> Agent:
    """Manager agent that synthesizes results from specialist agents."""
    return Agent(
        config=self.agents_config["report_writer"],
        # Manager agents typically don't delegate to avoid infinite loops
        allow_delegation=False
    )

@task
def compilation_task(self) -> Task:
    """Final task that receives all specialist agent outputs."""
    return Task(
        config=self.tasks_config["report_compilation_task"],
        agent=self.report_writer(),
        # Context includes ALL upstream tasks
        context=[
            self.web_research_task(),
            self.financial_analysis_task(),
            self.culture_investigation_task(),
            self.leadership_analysis_task(),
            self.career_growth_analysis_task()
        ]
    )
```

### Delegation Best Practices

1. **Specialist Agents**: Focus on specific domains, run async when possible
2. **Manager Agents**: Synthesize results, run synchronously as final task
3. **Context Flow**: Ensure manager agents receive all relevant specialist outputs
4. **Avoid Circular Dependencies**: Manager agents should not delegate back to specialists

## Process Handling

CrewAI supports multiple process modes for different coordination patterns:

### Process.sequential

Tasks execute one after another in defined order:

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=[self.agent1(), self.agent2()],
        tasks=[self.task1(), self.task2()],
        process=Process.sequential,  # Tasks run in order
        verbose=True
    )
```

**Use When**:
- Tasks have strict dependencies
- Later tasks need complete results from earlier tasks
- Simple linear workflows

### Process.hierarchical

Manager agent coordinates and delegates to specialist agents:

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=[
            self.specialist1(),
            self.specialist2(),
            self.manager()  # Manager must be last
        ],
        tasks=[
            self.analysis_task1(),
            self.analysis_task2(),
            self.synthesis_task()  # Final synthesis task
        ],
        process=Process.hierarchical,
        manager_agent=self.manager(),  # Specify manager
        verbose=True
    )
```

**Use When**:
- Complex workflows with multiple parallel analyses
- Need coordination between specialist agents
- Final synthesis/compilation step required

### Process.parallel

All tasks execute simultaneously:

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=[self.agent1(), self.agent2()],
        tasks=[self.task1(), self.task2()],
        process=Process.parallel,  # All tasks run together
        verbose=True
    )
```

**Use When**:
- Independent tasks with no dependencies
- Maximum speed required
- Simple parallel processing

### Choosing the Right Process

1. **Sequential**: Simple workflows, strict dependencies
2. **Hierarchical**: Complex analysis with synthesis (recommended for most cases)
3. **Parallel**: Independent tasks only

## FastAPI Integration

### Step 1: Create Schemas

Define request/response models in `app/schemas/`:

```python
# app/schemas/company.py
from pydantic import BaseModel
from typing import Dict, Any

class CompanyRequest(BaseModel):
    company_name: str

class CompanyReportResponse(BaseModel):
    report: Dict[str, Any]
```

### Step 2: Create Service Function

Create service function in `app/services/`:

```python
# app/services/company_service.py
from ..services.crewai.research_company import get_research_company_crew

def generate_company_report(company_name: str) -> Dict[str, Any]:
    """Generate comprehensive company research report."""
    crew = get_research_company_crew()
    
    inputs = {"company_name": company_name}
    result = crew.kickoff(inputs=inputs)
    
    return result
```

### Step 3: Create API Endpoint

Create endpoint in `app/api/v1/endpoints/`:

```python
# app/api/v1/endpoints/company.py
from fastapi import APIRouter, HTTPException
from ....schemas.company import CompanyRequest, CompanyReportResponse
from ....services.company_service import generate_company_report

router = APIRouter(prefix="/company", tags=["Company Research"])

@router.post("/report", response_model=CompanyReportResponse)
async def company_report(request: CompanyRequest):
    """Generate comprehensive company research report."""
    try:
        report = generate_company_report(request.company_name)
        return CompanyReportResponse(report=report)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 4: Register Router

Add router to main API in `app/api/v1/api.py`:

```python
from .endpoints import company

api_router.include_router(company.router)
```

### FastAPI Integration Guidelines

1. **Async Functions**: Always use `async def` for FastAPI endpoints
2. **Error Handling**: Catch and convert exceptions to appropriate HTTP codes
3. **Input Validation**: Use Pydantic models for request validation
4. **Response Models**: Define response schemas for consistent API contracts
5. **Router Organization**: Group related endpoints in dedicated router modules

## Crew Implementation Template

Use this template for creating new crews:

```python
# app/services/crewai/{crew_name}/crew.py
from threading import Lock
from typing import Optional
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from ..base import load_agent_config, load_tasks_config, get_shared_tools

_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

@CrewBase
class {CrewName}Crew:
    """
    {Description of crew purpose and functionality}
    
    This crew follows the standard multi-agent pattern with specialist
    agents coordinated by a manager agent for final synthesis.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def specialist_agent(self) -> Agent:
        """Specialist agent for specific domain analysis."""
        return Agent(
            config=self.agents_config["specialist_agent"],
        )

    @agent
    def manager_agent(self) -> Agent:
        """Manager agent that synthesizes specialist results."""
        return Agent(
            config=self.agents_config["manager_agent"],
        )

    @task
    def analysis_task(self) -> Task:
        """Specific analysis task."""
        return Task(
            config=self.tasks_config["analysis_task"],
            agent=self.specialist_agent(),
            async_execution=True
        )

    @task
    def synthesis_task(self) -> Task:
        """Final synthesis task."""
        return Task(
            config=self.tasks_config["synthesis_task"],
            agent=self.manager_agent(),
            context=[self.analysis_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Assemble the complete crew."""
        return Crew(
            agents=[
                self.specialist_agent(),
                self.manager_agent()
            ],
            tasks=[
                self.analysis_task(),
                self.synthesis_task()
            ],
            process=Process.hierarchical,
            verbose=True,
        )

def get_{crew_name}_crew() -> Crew:
    """Factory function with singleton pattern for crew instances."""
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = {CrewName}Crew().crew()
    assert _cached_crew is not None
    return _cached_crew
```

## Environment Configuration

### Required Environment Variables

```bash
# CrewAI Configuration
CREWAI_MOCK_MODE=false              # Enable mock mode for testing
LLM_PREFERENCE=openai               # Preferred LLM provider

# MCP Integration
MCP_GATEWAY_ENABLED=true            # Enable MCP gateway
MCP_GATEWAY_URL=http://mcp-gateway:8811  # MCP gateway URL

# Tool Configuration
DUCKDUCKGO_API_KEY=your_key         # For web search tools
OPENAI_API_KEY=your_key             # For OpenAI models
```

### Configuration Loading

Use the base utilities for consistent configuration loading:

```python
from ..base import load_agent_config, load_tasks_config, get_mock_mode

# Load agent configuration
config = load_agent_config(Path(__file__).parent.parent, "agent_name")

# Load tasks configuration  
tasks = load_tasks_config(Path(__file__).parent, "crew_name")

# Check mock mode
if get_mock_mode():
    # Return mock responses for testing
    pass
```

## Testing and Validation

### Unit Testing Pattern

```python
# tests/services/test_{crew_name}_crew.py
import pytest
from unittest.mock import patch
from app.services.crewai.{crew_name} import get_{crew_name}_crew

class Test{CrewName}Crew:
    """Test suite for {CrewName}Crew functionality."""
    
    @patch.dict('os.environ', {'CREWAI_MOCK_MODE': 'true'})
    def test_crew_initialization(self):
        """Test that crew initializes properly in mock mode."""
        crew = get_{crew_name}_crew()
        assert crew is not None
        assert len(crew.agents) > 0
        assert len(crew.tasks) > 0
    
    def test_crew_execution_with_valid_input(self):
        """Test crew execution with valid inputs."""
        crew = get_{crew_name}_crew()
        inputs = {"required_field": "test_value"}
        
        result = crew.kickoff(inputs=inputs)
        assert result is not None
        # Add specific assertions based on expected output
```

### Integration Testing

```python
# tests/integration/test_{crew_name}_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class Test{CrewName}Integration:
    """Integration tests for {CrewName} API endpoints."""
    
    def test_{crew_name}_endpoint(self):
        """Test the API endpoint integration."""
        response = client.post(
            "/{crew_name}/endpoint",
            json={"required_field": "test_value"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
```

## Maintenance Requirements

### Critical Update Requirements

**This AGENT.md file MUST be updated whenever:**

1. **Crew Structure Changes**:
   - New crews added or existing crews modified
   - Agent definitions changed in YAML files
   - Task configurations updated
   - Process modes changed

2. **YAML Configuration Changes**:
   - New fields added to agent or task configurations
   - Configuration patterns modified
   - Shared agent patterns updated

3. **FastAPI Integration Changes**:
   - New API endpoints added
   - Endpoint patterns modified
   - Request/response schemas changed
   - Error handling patterns updated

4. **Architecture Changes**:
   - New patterns introduced
   - File structure modifications
   - Tool integration changes
   - Environment variable changes

### Update Process

1. **Immediate Documentation**: Update this file BEFORE implementing changes
2. **Pattern Consistency**: Ensure new implementations follow established patterns
3. **Example Updates**: Update code examples to reflect current patterns
4. **Validation**: Test that examples in this document work with current codebase
5. **Review Process**: Have changes reviewed for consistency with established patterns

### Version Control

- Tag this file in git when major architectural changes are made
- Include documentation updates in the same commit as code changes
- Reference this document in pull request descriptions for CrewAI changes

## Troubleshooting

### Common Issues

1. **Agent Configuration Not Loading**:
   - Check file paths in `agents_config` and `tasks_config`
   - Verify YAML syntax with a validator
   - Ensure required fields are present

2. **Task Dependencies Not Working**:
   - Verify context task names match task method names
   - Check that prerequisite tasks complete successfully
   - Review async_execution settings for dependent tasks

3. **Crew Execution Failures**:
   - Enable verbose mode for detailed logging
   - Check environment variables are set
   - Verify tool configurations and API keys

4. **FastAPI Integration Issues**:
   - Ensure request/response models match crew inputs/outputs
   - Check error handling covers all exception types
   - Verify router registration in main API

### Debug Mode

Enable debug logging and mock mode for development:

```bash
export CREWAI_MOCK_MODE=true
export LOG_LEVEL=DEBUG
```

This provides detailed execution logs without making external API calls.

### Result Parsing

- Use `parse_crew_result` to extract JSON from `crew.kickoff` outputs.
- Parsed data must include `final`, `personas`, `tradeoffs`, `actions`, `sources`, and at least one score field. Additional metrics are surfaced under a `data` key while `final.rationale` stays concise.
- Text heuristics are used only when parsing fails.

---

**Remember**: This AGENT.md file is a living document that must evolve with the codebase. Keep it updated, accurate, and actionable for future AI agents and developers working with CrewAI implementations.