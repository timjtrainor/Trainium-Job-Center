# AGENTS.md — Job Posting Review Service

**Purpose**: Orchestrates the job posting review pipeline using CrewAI multi-agent architecture with YAML-first design.

## Python Orchestration

The crew runs its evaluation pipeline directly in Python via the `run_orchestration` method in `crew.py`. YAML files define all agents and tasks. `managing_agent` and `orchestration_task` remain only for backward compatibility and are not registered in the crew.

### Task Sequence

1. `intake_task` – parse raw job posting text into normalized fields.
2. `pre_filter_task` – apply rule-based rejection criteria; stop on `recommend=false`.
3. `quick_fit_task` – lightweight scoring for jobs that pass the pre-filter.
4. `brand_match_task` – compare job attributes to the candidate's career brand framework.

`run_orchestration` constructs a fresh crew instance and retrieves tasks from `crew.tasks` so each agent is bound before sequential execution. It returns a JSON object validated by the `JobPostingReviewOutput` Pydantic model containing `job_intake`, `pre_filter`, `quick_fit`, and `brand_match`.

## Entrypoints

- `run_crew(job_posting_data, options, correlation_id)` – FastAPI routes call this function to run the evaluation pipeline.
- `JobPostingReviewCrew.run_orchestration(job_posting_data)` – Primary orchestration method.
- `crew.kickoff(inputs={job_posting_data, options})` – Lower-level crew execution for testing and debugging.

## YAML Configuration

**agents.yaml**

- `job_intake_agent` – parse job posting into structured JSON.
- `pre_filter_agent` – apply three rejection rules.
- `quick_fit_analyst` – score career growth, compensation, lifestyle, and purpose alignment.
- `brand_framework_matcher` – evaluate alignment with the candidate's career brand framework.
- `managing_agent` – legacy agent supporting the unused `orchestration_task`.

**tasks.yaml**

- `intake_task` – bound to `job_intake_agent`.
- `pre_filter_task` – bound to `pre_filter_agent`.
- `quick_fit_task` – bound to `quick_fit_analyst`.
- `brand_match_task` – bound to `brand_framework_matcher`.
- `orchestration_task` – legacy task; present for compatibility but not executed.

Agent and task identifiers in YAML must match method names in `crew.py`.

## Output Contract

`run_orchestration` returns:

```json
{
  "job_intake": {},
  "pre_filter": {"recommend": true, "reason": "..."},
  "quick_fit": {},
  "brand_match": {}
}
```

If `pre_filter.recommend` is `false`, `quick_fit` and `brand_match` are `null`. The result is validated by `JobPostingReviewOutput`.

---

This document must be updated whenever agent definitions, task configurations, or orchestration behavior changes.

