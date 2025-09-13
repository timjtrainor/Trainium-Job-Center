# AGENT.md — Fit Review Service

**Purpose**: Orchestrates the job_posting_fit_review crew using CrewAI multi-agent architecture with YAML-first design.

**Entrypoints**:
- `orchestrator.run(job_posting, options)` → main entry for FastAPI routes
- `judge.decide(verdicts, weights, guardrails, job_meta)` → deterministic aggregation of persona verdicts
- `normalize_jd(text)` → safe HTML cleaning and text deduplication 
- `get_career_brand_digest(profile_id, k, threshold)` → ChromaDB career insights query
- `build_context(job_posting, profile_id)` → complete input preparation for YAML crews

## Retrieval Layer

**Purpose**: Prepares inputs for YAML-defined CrewAI tasks. The retrieval layer normalizes job descriptions and queries ChromaDB for career insights, returning structured data that crew.py forwards to YAML placeholders.

**Core Functions**:

### `normalize_jd(text: str) -> str`
- Safely removes HTML using Bleach sanitizer and selectolax parser (documented at https://bleach.readthedocs.io/ and https://selectolax.readthedocs.io/)
- Collapses whitespace and deduplicates identical bullet points
- Returns clean text suitable for LLM prompts
- Deterministic output for same inputs

### `get_career_brand_digest(profile_id, k=8, threshold=0.2) -> dict`  
- Connects to ChromaDB using project's configured client
- Queries "career_brand" collection following documented API (https://docs.trychroma.com/usage-guide#querying-a-collection)
- Returns `{digest, doc_ids, scores, metadata}` with ~2000 token budget
- Graceful handling when collection is empty/unavailable

### `build_context(job_posting, profile_id) -> dict`
- Orchestrates normalize_jd + get_career_brand_digest 
- Extracts domain/seniority tags using simple heuristics
- Returns `{normalized_jd, career_brand_digest, doc_ids, scores, tags, metadata}`
- Keys align with YAML placeholder expectations

**YAML-First Design**: All agent/task orchestration lives in YAML files (agents.yaml, tasks.yaml). The retrieval layer only prepares data that crew.py forwards to YAML placeholders like `{job_description}`, `{career_brand_digest}`, and `{job_meta}`. CrewAI's documentation explicitly recommends YAML for agents/tasks with runtime variable interpolation: https://docs.crewai.com/how-to/Creating-a-Crew-and-kick-it-off/

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
- ✅ Do: Keep HTML cleaning safe and deterministic using Bleach or fast parser (selectolax)
- ✅ Do: Ensure digest respects token/length budgets (~2000 chars)
- ✅ Do: Add new helpers in `helpers/` with compact JSON contracts
- ✅ Do: Use the retrieval service for preprocessing before persona evaluation
- ✅ Do: Implement deterministic aggregation logic in judge
- ❌ Don't: Call external web APIs from retrieval; research happens via designated helper agents on YAML side
- ❌ Don't: Modify the YAML files; retrieval returns data only
- ❌ Don't: Put business logic in route layer; keep routes thin
- ❌ Don't: Hardcode weights or guardrails; use configuration
- ❌ Don't: Embed persona logic in retrieval; keep it pure data preparation