# AGENT.md — Fit Review Helper Agents

**Purpose**: Specialized persona agents that evaluate job postings from distinct decision-making perspectives.

**Entrypoints**:
- `DataAnalystHelper.evaluate(job_posting, context)` → data-focused evaluation
- `StrategistHelper.evaluate(job_posting, context)` → strategic career evaluation  
- `StakeholderHelper.evaluate(job_posting, context)` → collaboration assessment
- `TechnicalLeaderHelper.evaluate(job_posting, context)` → engineering leadership evaluation
- `RecruiterHelper.evaluate(job_posting, context)` → job quality and attractiveness assessment
- `SkepticHelper.evaluate(job_posting, context)` → risk and red flag identification
- `OptimizerHelper.evaluate(job_posting, context)` → opportunity optimization evaluation

**Contracts**:
- Input: `JobPosting` model + context dict (normalized job data, career brand digest)
- Output: `PersonaVerdict` model (id, recommend, reason, notes, sources)
- All evaluations are async and should be lightweight (< 5 seconds)

**Conventions**:
- Each helper focuses on specific decision lens and evaluation criteria
- Return structured verdicts with clear reasoning and supporting evidence
- Include sources for traceability (job_description, company_reviews, etc.)
- Use consistent logging pattern: persona_id, job_title, verdict
- Handle missing or incomplete data gracefully

**Do/Don't**:
- ✅ Do: Focus on your persona's specific expertise and decision lens
- ✅ Do: Provide actionable reasoning in verdict explanations
- ✅ Do: Include relevant notes and sources for transparency
- ✅ Do: Use consistent evaluation patterns across all helpers
- ❌ Don't: Make external API calls; use provided context data
- ❌ Don't: Override other personas' decision areas
- ❌ Don't: Return vague or generic recommendations