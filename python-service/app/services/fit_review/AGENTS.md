# AGENT.md — Fit Review Service

**Purpose**: Orchestrates the job_posting_fit_review crew using CrewAI multi-agent architecture.

**Entrypoints**:
- `orchestrator.run(job_posting, options)` → main entry for FastAPI routes
- `judge.decide(verdicts, weights, guardrails, job_meta)` → deterministic aggregation of persona verdicts
- `retrieval.normalize_jd` + `retrieval.get_career_brand_digest` → shared preprocessing for job data

**Contracts**:
- Input: `JobPosting` model (title, company, location, description, url)
- Output: `FitReviewResult` model (job_id, final recommendation, persona verdicts, tradeoffs, actions)
- Intermediate: `PersonaVerdict` from each helper agent

**Conventions**:
- Keep helper agent calls lightweight, return compact JSON structures
- Logging must include correlation_id for request tracing
- Guardrails/weights configurable via `config/weights_guardrails.yml`
- Use async/await for all operations to support parallel persona evaluation
- Handle errors gracefully with fallback to partial results when possible

**Do/Don't**:
- ✅ Do: Add new helpers in `helpers/` with compact JSON contracts
- ✅ Do: Use the retrieval service for preprocessing before persona evaluation
- ✅ Do: Implement deterministic aggregation logic in judge
- ❌ Don't: Call external APIs directly from orchestrator; use helpers or retrieval
- ❌ Don't: Put business logic in route layer; keep routes thin
- ❌ Don't: Hardcode weights or guardrails; use configuration