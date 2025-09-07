# CrewAI YAML Configuration Guide

This document explains the restructured CrewAI setup where agent definitions have been moved from Python code into YAML configuration files.

## Overview

The CrewAI system now uses two main YAML files:

- **`app/services/ai/persona_catalog.yaml`** - Defines agent personas with their roles, behaviors, and CrewAI parameters
- **`app/services/ai/tasks.yaml`** - Defines tasks that can be executed by personas, including persona review tasks

## app/services/ai/persona_catalog.yaml Structure

### CrewAI Standard Fields (Top Level)
These fields are directly used by CrewAI for agent creation:

```yaml
advisory:
  - id: headhunter
    role: "Market scout finding emerging roles"           # CrewAI agent role
    goal: "Scout emerging job roles..."                   # CrewAI agent goal  
    backstory: "A veteran headhunter who tracks..."       # CrewAI agent backstory
    max_iter: 3                                          # CrewAI max iterations
    max_execution_time: 60                               # CrewAI timeout (seconds)
    tools: [web_search]                                  # CrewAI tool names
    models: [...]                                        # LLM model configurations
```

### Custom Metadata Section
Persona-specific fields are stored under `metadata` to avoid conflicts with CrewAI parameters:

```yaml
    metadata:
      decision_lens: "Does this role give me an edge?"   # Decision-making perspective
      tone: bold                                         # Communication style
      capabilities: [market_intel, future_demand]       # Persona abilities
      crew_manifest_ref: headhunter.json                 # Reference file
```

## app/services/ai/tasks.yaml Structure

### Pre-tasks (Existing)
Analysis tasks that run before persona evaluations:

```yaml
pre_tasks:
  - id: skills_analysis
    builder: build_skills_task
    summary: "Analyze job posting to extract skills"
```

### Persona Review Tasks (New)
Tasks that execute persona-based evaluations:

```yaml
persona_review_tasks:
  - id: advisory_review
    agent: headhunter                                    # References persona ID
    description: "Analyze job from advisory perspective"
    expected_output: "Structured evaluation with vote"
    context: "Job posting data and resume context"
    async_execution: false
    markdown: true
    output_file: "advisory_review.md"                   # Optional file output
```

## Python Usage

### Loading Personas
```python
from app.services.persona_loader import PersonaCatalog

catalog = PersonaCatalog(Path("app/services/ai/persona_catalog.yaml"))
persona = catalog.get("headhunter")

# Get CrewAI agent configuration
agent_config = catalog.create_agent_config("headhunter")
```

### Loading Tasks  
```python
import yaml

with open("app/services/ai/tasks.yaml") as f:
    tasks = yaml.safe_load(f)
    
persona_tasks = tasks["persona_review_tasks"]
```

## Benefits

✅ **Maintainable**: Edit personas/tasks via YAML—no code changes needed  
✅ **Reusable**: YAML definitions work across different workflows  
✅ **Scalable**: Adding new personas/tasks is simple YAML editing  
✅ **Separation**: Python handles logic, YAML holds configuration  
✅ **CrewAI Compliant**: Proper separation of CrewAI vs custom parameters  

## Adding New Personas

1. Edit `app/services/ai/persona_catalog.yaml`
2. Add persona to appropriate group (advisory, motivational, decision, judge)
3. Include all required CrewAI fields at top level
4. Put custom fields under `metadata` section
5. Restart application to load changes

No Python code changes required!

## Tool Integration

Tools are defined by name in YAML:

```yaml
tools: [web_search, database_query]
```

Actual tool instances are resolved in Python using the tool names as references to imported tool objects.