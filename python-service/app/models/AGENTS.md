# AGENT.md — Business Models  

**Purpose**: Pydantic models for business logic and data validation in the fit review pipeline.

**Entrypoints**:
- `JobPosting` → input model for job postings to be evaluated
- `PersonaVerdict` → output model from individual persona helper agents
- `FitReviewResult` → complete output model with final recommendation
- `JudgeDecision` → internal model for judge aggregation logic
- `ConfidenceLevel` → enum for recommendation confidence levels

**Contracts**:
- All models use Pydantic v2 for validation and serialization
- Input models require all mandatory fields (title, company, location, description, url)
- Output models include optional fields for extensibility (notes, sources, tradeoffs, actions)
- Enums provide controlled vocabularies for confidence levels

**Conventions**:
- Use descriptive field names and comprehensive docstrings
- Include example data in Config.json_schema_extra for API documentation
- Validate URLs using Pydantic's HttpUrl type
- Use Optional[] for truly optional fields, not defaults
- Follow snake_case naming convention consistently

**Do/Don't**:
- ✅ Do: Add comprehensive field descriptions for API docs
- ✅ Do: Use appropriate Pydantic validators for data integrity
- ✅ Do: Include realistic examples in model configurations
- ✅ Do: Use enums for controlled vocabularies
- ❌ Don't: Add business logic methods to models; keep them as data containers
- ❌ Don't: Use generic field names like 'data' or 'info'
- ❌ Don't: Make fields optional when they should be required