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
├── base.py                       # Shared CrewBase utilities
├── agents/                       # Shared agent YAML configurations
├── tools/                        # Shared tool definitions (optional)
├── job_posting_review/           # Job posting review crew
│   ├── crew.py                   # JobPostingReviewCrew class
│   └── config/                   # YAML configurations
├── personal_branding/            # Personal branding crew
│   ├── crew.py                   # PersonalBrandCrew class
│   └── config/                   # YAML configurations
└── research_company/             # Company research crew
    ├── crew.py                   # ResearchCompanyCrew class
    └── config/                   # YAML configurations
```

## Current Implementation

### JobPostingReviewCrew

The `job_posting_review` crew provides structured analysis of job postings with multi-agent orchestration:

1. **Job Intake Agent** - Parses and structures job posting data
2. **Pre-filter Agent** - Applies rejection rules based on criteria  
3. **Quick Fit Analyst** - Analyzes career fit and alignment scores
4. **Brand Framework Matcher** - Evaluates brand alignment with career goals

### PersonalBrandCrew

The `personal_branding` crew helps with personal brand development and career positioning.

### ResearchCompanyCrew

The `research_company` crew provides comprehensive company research and analysis.

#### Usage

```python
from app.services.crewai.job_posting_review.crew import get_job_posting_review_crew
from app.services.crewai.personal_branding.crew import get_personal_brand_crew
from app.services.crewai.research_company.crew import get_research_company_crew

# Get crew instances
job_posting_crew = get_job_posting_review_crew()
personal_brand_crew = get_personal_brand_crew()
research_crew = get_research_company_crew()

# Execute job posting review
job_data = {
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "description": "Looking for experienced Python developer..."
}

result = job_posting_crew.run_orchestration(job_data)
```

#### API Endpoints

Current working crews provide endpoints for:
- Job posting review and fit analysis
- Personal branding assistance  
- Company research and analysis

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