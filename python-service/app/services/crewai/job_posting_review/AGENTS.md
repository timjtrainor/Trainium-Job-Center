# AGENTS.md — Job Posting Review Service

**Purpose**: Orchestrates the motivational evaluator fan-out system using CrewAI multi-agent architecture with YAML-first design and optional helper agent insights.

**Entrypoints**:
- `run_crew(job_posting_data, options, correlation_id)` → main entry for FastAPI routes executing motivational fan-out
- `MotivationalFanOutCrew.motivational_fanout()` → YAML-driven crew executing helper snapshot + five parallel evaluations  
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
- Uses placeholders: `{job_title}`, `{job_company}`, `{job_location}`, `{job_description}`, `{career_brand_digest}`, `{options}`, `{helper_snapshot}`
- Returns structured JSON: `{persona_id, recommend (boolean), reason (1-2 sentences), notes (array), sources (array)}`
- Emphasizes brevity to control token usage
- Each task assigned to corresponding agent with `async_execution: true` for parallel execution

### Crew Flow (crew.py)
- **Helper snapshot stage**: Conditionally runs helper agents based on `{options.use_helpers}`
- **Fan-out execution**: All five motivational tasks run independently with the same inputs
- **Result collection**: Individual verdicts collected into `motivational_verdicts` array
- **Error handling**: Failed tasks return `{recommend: false, reason: "insufficient signal"}`
- **Placeholder resolution**: CrewAI replaces `{placeholders}` from `crew.kickoff(inputs={...})` at runtime

## Helpers as Lightweight YAML Tools

**Purpose**: Advisory helper agents are defined in YAML as agents + tasks that return compact JSON used by motivational evaluators.

**Entrypoints**: 
- `helper_snapshot` (aggregates helper JSON)
- Individual helper tasks: `data_analyst_task`, `strategist_task`, `stakeholder_task`, `technical_leader_task`, `recruiter_task`, `skeptic_task`, `optimizer_task`

**Contracts**: Each helper returns a small JSON object with fixed keys; the aggregator merges them into `{helper_snapshot}`. Motivational tasks may read `{helper_snapshot}`.

### Helper Agent Definitions (agents.yaml)
- **data_analyst**: Compensation and Market Data Analyst - salary/TC benchmarks and company health indicators
- **strategist**: Industry Trend and Strategy Analyst - trend fit (industry/platform shifts, AI adoption)
- **stakeholder**: Cross-Functional Partnership Specialist - partnership risks/opportunities
- **technical_leader**: Technical Delivery and Architecture Advisor - delivery feasibility, architecture trade-offs
- **recruiter**: ATS and Keyword Optimization Specialist - ATS/keyword gaps against JD
- **skeptic**: Risk Assessment and Red Flag Analyst - red-flag scan (financial/legal/culture signals)
- **optimizer**: Application Enhancement Strategist - top three quick tweaks to strengthen application

Each helper agent has:
- `max_iter`: 1 (faster execution than motivational agents)
- `max_execution_time`: 30 seconds (shorter than motivational agents)
- Focused, specific role for compact output

### Helper Task Definitions (tasks.yaml)
Each helper task:
- Consumes same placeholders as motivational tasks: `{job_title}`, `{job_company}`, `{job_location}`, `{job_description}`, `{career_brand_digest}`, `{options}`
- Returns compact JSON (≤600 chars typical):
  - **data_analyst** → `{"tc_range": "...", "refs": ["..."]}`
  - **strategist** → `{"signals": ["..."], "refs": ["..."]}`
  - **stakeholder** → `{"partners": ["..."], "risks": ["..."]}`
  - **technical_leader** → `{"notes": ["..."]}`
  - **recruiter** → `{"keyword_gaps": ["..."]}`
  - **skeptic** → `{"redflags": ["..."]}`
  - **optimizer** → `{"top3": ["...", "...", "..."]}`
- On insufficient signal, returns valid empty-shape JSON (e.g., `{"redflags": []}`)
- Emphasizes brevity and determinism

### Helper Snapshot Aggregation
- **helper_snapshot task**: Runs selected subset of helper tasks and merges JSON into single compact object
- Conditional execution: if `{options.use_helpers}` is false/missing → returns `{}`
- If enabled → returns merged JSON: `{"data_analyst": {...}, "strategist": {...}, ...}`
- Size constraint: ≤1.5 KB typical to prevent token bloat
- Failure handling: individual helper failures produce empty JSON for that key; overall object remains valid

### Integration with Motivational Tasks
- All motivational tasks receive `{helper_snapshot}` placeholder
- Task prompts include: "If helper_snapshot contains useful keys for your lens, cite them briefly in your reason; otherwise proceed without helpers"
- Motivational tasks remain robust with or without helper data
- Helper insights appear as brief citations in `reason` field, not verbose integration

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
    "options": {                 # Maps to {options}
        "use_helpers": bool,     # Controls helper execution
        ...                      # Other options
    }
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
    ],
    "helper_snapshot": {
        "data_analyst": {"tc_range": "...", "refs": [...]},
        "strategist": {"signals": [...], "refs": [...]},
        // ... other helpers or {} if disabled
    }
}
```

## YAML-First Guidance

**Critical Requirements**:
- All helper behavior (prompts, expected output, brevity constraints) is declared in YAML
- `crew.py` only passes inputs and binds configs - no helper logic in Python code
- Agent names in `agents.yaml` must exactly match method names in `crew.py`
- Task names in `tasks.yaml` must match method names for proper binding
- Placeholder names must match input keys exactly for CrewAI interpolation

**Do/Don't for Helpers**:
- ✅ **Do**: Keep helper responses ≤600 chars typical and strictly JSON
- ✅ **Do**: Handle missing data by returning empty structures, not prose
- ✅ **Do**: Use deterministic output patterns for reliable integration
- ✅ **Do**: Keep helper execution fast (≤30 seconds, 1 iteration max)
- ❌ **Don't**: Call external web APIs from Python here; if research is required, do it via YAML helper with clear output keys
- ❌ **Don't**: Reference helpers directly from FastAPI route; use through crew execution only
- ❌ **Don't**: Return verbose prose from helpers; stick to compact JSON structures
- ❌ **Don't**: Embed helper logic in Python; keep it YAML-declared

**Change Management**: If you rename helper IDs or task names, update `agents.yaml`, `tasks.yaml`, `crew.yaml`, and any tests that assert on those names to avoid binding mismatches.

## Validation and Error Behavior

**Task Failure Handling**:
- If any motivational task fails or times out → `{recommend: false, reason: "insufficient signal"}`
- If any helper task fails → empty JSON for that helper key in aggregated snapshot
- All five motivational tasks must produce parseable JSON → fail fast on malformed output
- Deterministic fallback behavior maintains system reliability

**Helper Failure Resilience**:
- Individual helper failures don't block motivational evaluation
- helper_snapshot returns valid JSON even with partial helper failures
- Motivational tasks work robustly with empty `{helper_snapshot: {}}`
- Size limits enforced to prevent token bloat (1.5 KB helper snapshot limit)

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
- Helper outputs especially compact (≤600 chars individual, ≤1.5 KB aggregated)

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
- ✅ Do: Use helpers conditionally based on `options.use_helpers`
- ✅ Do: Keep helper insights brief in motivational reasoning
- ❌ Don't: Change agent/task names without updating both YAML and Python bindings
- ❌ Don't: Return verbose prose from agents; stick to structured JSON
- ❌ Don't: Assume all tasks will succeed; implement robust error handling
- ❌ Don't: Hardcode agent logic in Python; keep it YAML-driven
- ❌ Don't: Modify YAML structure without verifying CrewAI compatibility
- ❌ Don't: Let helper payload exceed size limits (600 chars individual, 1.5 KB total)
- ❌ Don't: Make motivational tasks dependent on helper success