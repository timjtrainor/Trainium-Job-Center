# AGENTS.md — Job Posting Review Service

**Purpose**: Orchestrates the motivational evaluator fan-out system using CrewAI multi-agent architecture with YAML-first design.

**Entrypoints**:
- `run_crew(job_posting_data, options, correlation_id)` → main entry for FastAPI routes executing motivational fan-out
- `MotivationalFanOutCrew.motivational_fanout()` → YAML-driven crew executing five parallel evaluations  
- `crew.kickoff(inputs={job_posting_data, career_brand_digest, options})` → crew execution with placeholder replacement

## YAML-First Motivational Fan-Out

**Purpose**: All Motivational agents (builder, maximizer, harmonizer, pathfinder, adventurer) are defined in YAML files with runtime variable interpolation. The fan-out executes five independent evaluations that return thumbs-up/thumbs-down verdicts.

**Core Architecture**:

### Agent Definitions (agents.yaml)
- **builder**: Technical Builder and Systems Designer - evaluates technical building opportunities
- **maximizer**: Growth and Performance Optimizer - assesses growth and compensation potential  
- **harmonizer**: Culture and Team Harmony Specialist - determines cultural fit and team dynamics
- **pathfinder**: Career Path Navigator and Strategic Planner - evaluates career trajectory alignment
- **adventurer**: Innovation and Learning Explorer - assesses learning and innovation opportunities

Each agent has:
- `role`: Concise professional role description
- `goal`: Specific evaluation objective  
- `backstory`: Context and motivation for the agent
- `max_iter`: Maximum iterations (default: 2)
- `max_execution_time`: Timeout in seconds (default: 45)

### Task Definitions (tasks.yaml)
- **{persona}_evaluation**: Reusable task pattern for each motivational agent
- Uses placeholders: `{job_title}`, `{job_company}`, `{job_location}`, `{job_description}`, `{career_brand_digest}`, `{options}`
- Returns structured JSON: `{persona_id, recommend (boolean), reason (1-2 sentences), notes (array), sources (array)}`
- Emphasizes brevity to control token usage
- Each task assigned to corresponding agent with `async_execution: true` for parallel execution

### Crew Flow (crew.py)
- **Fan-out execution**: All five tasks run independently with the same inputs
- **Result collection**: Individual verdicts collected into `motivational_verdicts` array
- **Error handling**: Failed tasks return `{recommend: false, reason: "insufficient signal"}`
- **Placeholder resolution**: CrewAI replaces `{placeholders}` from `crew.kickoff(inputs={...})` at runtime

## Input Contract

**Required inputs for crew.kickoff():**
```python
inputs = {
    "job_posting_data": {
        "title": str,       # Maps to {job_title}
        "company": str,     # Maps to {job_company}  
        "location": str,    # Maps to {job_location}
        "description": str  # Maps to {job_description}
    },
    "career_brand_digest": str,  # Maps to {career_brand_digest}
    "options": dict              # Maps to {options}
}
```

**Output Contract:**
```python
{
    "motivational_verdicts": [
        {
            "persona_id": "builder|maximizer|harmonizer|pathfinder|adventurer",
            "recommend": boolean,
            "reason": "1-2 sentence explanation",
            "notes": ["key observation 1", "key observation 2"],
            "sources": ["job_description", "analysis_type"]
        }
    ]
}
```

## Validation and Error Behavior

**Task Failure Handling**:
- If any motivational task fails or times out → `{recommend: false, reason: "insufficient signal"}`
- All five tasks must produce parseable JSON → fail fast on malformed output
- Deterministic fallback behavior maintains system reliability

**JSON Parsing**:
- Primary: Extract JSON object matching expected schema from task output
- Fallback: Text parsing for boolean recommendation and reason extraction
- Error: Return `{recommend: false, reason: "insufficient signal", notes: ["task execution failed"]}`

## YAML Binding Rules

**Critical Requirements**:
- Agent names in `agents.yaml` must exactly match method names in `crew.py` (e.g., `builder` → `builder_agent()`)
- Task names in `tasks.yaml` must match method names (e.g., `builder_evaluation` → `builder_evaluation_task()`)
- Placeholder names in tasks must match input keys exactly (`{job_title}` requires `inputs["job_title"]`)
- Changes to agent/task IDs require updates in both YAML and Python to avoid KeyError binding issues

**CrewAI YAML Integration**:
- Follows CrewAI's documented pattern: agents/tasks defined in YAML, loaded by CrewBase-derived class
- Runtime variable interpolation via `crew.kickoff(inputs={...})` replaces `{placeholders}`
- Agent configurations loaded via custom `_load_agents_config()` and `_load_tasks_config()` methods
- LLM routing handled by `_RouterLLM` adapter compatible with project's `LLMRouter`

## Conventions

**Output Structure**:
- Keep agent outputs compact and structured JSON only
- No prose walls or verbose explanations
- 1-2 sentence reasons maximum for token efficiency
- Notes array for key observations, sources array for attribution

**Error Resilience**:
- Individual task failures don't block other evaluations
- Graceful degradation with partial results
- Deterministic fallback responses for consistent behavior
- Correlation ID tracking for debugging and monitoring

**Do/Don't**:
- ✅ Do: Keep YAML agent definitions stable once bound to avoid runtime errors
- ✅ Do: Use exact placeholder names in tasks that match input preparation
- ✅ Do: Return compact JSON structures for efficient processing
- ✅ Do: Handle task failures gracefully with "insufficient signal" responses
- ✅ Do: Log execution with correlation IDs for traceability
- ❌ Don't: Change agent/task names without updating both YAML and Python bindings
- ❌ Don't: Return verbose prose from agents; stick to structured JSON
- ❌ Don't: Assume all tasks will succeed; implement robust error handling
- ❌ Don't: Hardcode agent logic in Python; keep it YAML-driven
- ❌ Don't: Modify YAML structure without verifying CrewAI compatibility