# Job Posting Review - Refactored CrewAI Architecture

## Overview

This module provides a refactored CrewAI-based job posting evaluation system with clean separation of concerns between orchestration, business logic, and agent configuration.

## Architecture

The refactored architecture follows a three-layer approach:

### 1. **Orchestrator Layer** (`orchestrator.py`)
- **Purpose**: Workflow coordination and CrewAI execution
- **Responsibilities**:
  - Input validation using Pydantic models
  - Execution of evaluation pipeline
  - Result parsing and structuring
  - Error handling and graceful fallbacks

### 2. **Crew Layer** (`crew.py`)
- **Purpose**: Pure CrewAI agent and task definitions
- **Responsibilities**:
  - Agent configuration via YAML
  - Task definitions with business logic in configurations
  - Clean, focused crew assembly

### 3. **Data Layer** (`rules.py`)
- **Purpose**: Data models and utility functions
- **Responsibilities**:
  - Pydantic input/output validation
  - Utility functions for ID generation, deduplication
  - JSON parsing helpers

## Workflow

1. **Pre-filter Stage**: Rule-based rejection of unqualified jobs
2. **Parallel Analysis**: ChromaDB-powered evaluation across 5 career dimensions
3. **Synthesis**: Weighted scoring and final recommendation

### Career Dimensions Analyzed:
- **North Star & Vision**: Long-term career goals alignment
- **Trajectory & Mastery**: Skill development and expertise growth
- **Values Compass**: Cultural and value system alignment
- **Lifestyle Alignment**: Work-life balance preferences
- **Compensation Philosophy**: Financial expectations and requirements

## Usage

### High-Level API (Recommended)
```python
from app.services.crewai.job_posting_review import evaluate_job_posting

result = evaluate_job_posting(job_posting_dict, correlation_id="optional_id")
```

### Direct Orchestrator Access
```python
from app.services.crewai.job_posting_review import JobPostingOrchestrator

orchestrator = JobPostingOrchestrator()
result = await orchestrator.evaluate_job_posting_async(job_posting_dict)
```

### Crew-Only Access (Advanced)
```python
from app.services.crewai.job_posting_review import get_job_posting_review_crew

crew = get_job_posting_review_crew()
# Configure inputs and execute manually
```

## Configuration

### Agent Configuration (`config/agents.yaml`)
- Pre-filter agent for rule-based rejection
- 5 brand dimension specialists (parallel execution)
- Brand match manager for synthesis

### Task Configuration (`config/tasks.yaml`)
- Pre-filter task with rejection rules
- Parallel brand dimension analysis tasks
- Synthesis task with weighted scoring

## Key Benefits

- **Separation of Concerns**: Business logic in agents, orchestration in dedicated layer
- **Testability**: Each layer can be tested independently
- **Maintainability**: Clear module boundaries and responsibilities
- **Scalability**: Easy to add new career dimensions or rejection rules
- **Type Safety**: Pydantic validation throughout the pipeline
- **Performance**: Parallel agent execution with proper async coordination
- **CrewAI Knowledge Integration**: Native ChromaDB knowledge access instead of custom tools

## ChromaDB Knowledge Integration

The system now uses **CrewAI's built-in knowledge functionality** instead of custom search tools:

### Knowledge Source Configuration
Each brand dimension specialist agent has knowledge sources configured to access the `career_brand` collection:

```yaml
knowledge_sources:
  - type: chroma
    config:
      host: "chromadb"  # Uses CHROMA_URL env var
      port: 8000        # Uses CHROMA_PORT env var
      collection: "career_brand"
      filters:
        section: "north_star_vision"
        latest_version: true
```

### Latest Version Filtering
Documents in the `career_brand` collection should include metadata for version control:

```python
metadata = {
  "section": "north_star_vision",  # One of: north_star_vision, trajectory_mastery, values_compass, lifestyle_alignment, compensation_philosophy
  "latest_version": true,          # Boolean flag for latest document per section
  "timestamp": "2025-09-28T14:00:00Z",  # ISO timestamp
  "version": "2025-09-28"          # Optional version identifier
}
```

### Environment Variable Configuration
ChromaDB connection parameters are pulled from environment variables:

- `CHROMA_URL=chromadb` - Docker service name
- `CHROMA_PORT=8000` - ChromaDB port

## Error Handling

The orchestrator provides graceful error handling:
- Input validation errors return structured error responses
- CrewAI execution failures return partial results with error details
- All responses maintain consistent structure for API compatibility

## Business Logic Location

**Important**: All business logic (rejection rules, scoring algorithms, decision thresholds) remains in the CrewAI agent/task YAML configurations. The Python code focuses on:

- Workflow coordination
- Data validation and transformation
- Error handling and result formatting
- Utility functions and helpers

This preserves the CrewAI agent-based evaluation while providing better code organization and maintainability.
