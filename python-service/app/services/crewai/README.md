# CrewAI Service - Scalable Multi-Crew Architecture

This directory contains the CrewAI service implementation following best practices for scalable multi-crew systems with YAML-driven configuration.

## Architecture Overview

The CrewAI service is organized using a scalable multi-crew pattern where each crew has its own directory containing:
- `crew.py` - Crew class with agents and tasks using CrewAI decorators
- `tasks.yaml` - YAML configuration for crew-specific tasks

Shared resources are organized at the service level:
- `agents/` - Shared agent YAML configurations
- `tools/` - Shared tool definitions (optional)
- `base.py` - Common utilities and base classes

## Directory Structure

```
app/services/crewai/
├── base.py                    # Shared CrewBase utilities
├── agents/                    # Shared agent YAML configurations
│   ├── researcher.yaml        # Research and analysis agent
│   ├── negotiator.yaml        # Compensation analysis agent
│   └── skeptic.yaml           # Quality assessment agent
├── tools/                     # Shared tool definitions (optional)
├── job_review/                # Job analysis crew
│   ├── crew.py                # JobReviewCrew class
│   └── tasks.yaml             # Job review tasks configuration
├── resume_review/             # Resume analysis crew (future)
│   ├── crew.py
│   └── tasks.yaml
└── interview_prep/            # Interview preparation crew (future)
    ├── crew.py
    └── tasks.yaml
```

## Current Implementation

### JobReviewCrew

The `job_review` crew provides comprehensive analysis of job postings using three specialized agents:

1. **Researcher Agent** - Analyzes skills, requirements, and experience levels
2. **Negotiator Agent** - Evaluates compensation, benefits, and market positioning  
3. **Skeptic Agent** - Assesses quality, completeness, and identifies red/green flags

#### Usage

```python
from app.services.crewai import get_job_review_crew

# Get crew instance
crew = get_job_review_crew()

# Execute analysis
job_data = {
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "description": "Looking for experienced Python developer..."
}

result = crew.job_review().kickoff(inputs={"job": job_data})
```

#### API Endpoints

- `POST /jobs/review` - Analyze single job
- `POST /jobs/review/batch` - Analyze multiple jobs
- `GET /jobs/review/from-db` - Analyze jobs from database
- `GET /jobs/review/agents` - Get available agents info
- `GET /jobs/review/health` - Service health check

## Configuration

### Agent Configuration (YAML)

Each agent is defined in a YAML file in the `agents/` directory:

```yaml
version: "1.0"
id: researcher
persona_type: Advisory
role: "Desk researcher using Google Search for insight"
goal: "Surface quick facts that inform the job decision."
backstory: "An inquisitive researcher who quickly gathers facts from the web."
max_iter: 2
max_execution_time: 30
tools:
  - web_search
metadata:
  decision_lens: "What quick facts can guide this decision?"
  tone: inquisitive
  capabilities:
    - google_search
models:
  - provider: ollama
    model: gemma3:1b
```

### Task Configuration (YAML)

Each crew defines its tasks in a `tasks.yaml` file:

```yaml
version: "1.0"

tasks:
  skills_analysis:
    id: skills_analysis
    description: "Research and analyze job posting to extract skills..."
    expected_output: "Structured analysis of required skills..."
    agent: researcher
    context: "Raw job posting text and metadata"
    async_execution: false
    markdown: false

execution_sequence:
  - skills_analysis
  - compensation_analysis
  - quality_assessment
```

## Best Practices

### CrewBase Implementation

All crews inherit from `CrewAIBase` which provides:
- YAML configuration loading utilities
- Shared error handling and logging
- Mock mode support for testing
- Consistent initialization patterns

### Decorators Usage

- Use `@agent` decorator for agent definitions
- Use `@task` decorator for task definitions  
- Use `@crew` decorator for crew assembly
- Use `@before_kickoff` and `@after_kickoff` for lifecycle hooks

### Error Handling and Logging

- All configuration loading includes proper error handling
- Logging uses loguru for structured output
- Mock mode available via `CREWAI_MOCK_MODE` environment variable

## Adding New Crews

1. Create a new directory under `crewai/` (e.g., `resume_review/`)
2. Create `crew.py` with crew class inheriting from `CrewAIBase`
3. Create `tasks.yaml` with crew-specific task configurations
4. Add any new shared agents to `agents/` directory
5. Update the main `__init__.py` to export the new crew

## Environment Variables

- `CREWAI_MOCK_MODE` - Enable mock mode for testing (default: false)
- `LLM_PREFERENCE` - Configure preferred LLM providers
- Other environment variables as defined in `app/core/config.py`

## Future Enhancements

- Resume analysis crew for candidate evaluation
- Interview preparation crew for question generation
- Custom scoring models per crew type
- Enhanced tool integrations
- Performance monitoring and analytics