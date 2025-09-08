# AGENT.md — FastAPI Routes

**Purpose**: Serve as thin HTTP access point for the YAML-configured CrewAI pipeline.

**Entrypoint**: `POST /jobs/posting/fit_review` - Delegates execution entirely to the YAML-defined CrewAI crew.

**Data Contracts**: 
- Input: `JobPosting` model (title, company, location, description, url)
- Output: `FitReviewResult` model (job_id, final recommendation, personas, tradeoffs, actions, sources)

**YAML-centric Design**: Business logic and orchestration are defined via `agents.yaml`, `tasks.yaml`, and resolved via `crew.py`. This route contains NO hardcoded orchestration logic - it delegates entirely to `run_crew` function.

**Error Handling**:
- Pydantic validation - automatic 422 response
- Crew execution failures - HTTP 500 with structured error including correlation_id
- All errors logged with correlation_id for traceability

**Logging**: 
- Structured logging with correlation_id, route path, and elapsed time in ms
- Request entry/exit logging for monitoring and debugging

**Do/Don't**:
- ✅ Do: Call `run_crew` and delegate entirely to YAML-defined crew
- ✅ Do: Generate correlation_id for request tracking
- ✅ Do: Log structured data with timing information
- ✅ Do: Return structured error responses with correlation_id
- ❌ Don't: Add orchestration logic, job parsing, or persona coordination here
- ❌ Don't: Implement business logic in the route - keep it thin
- ❌ Don't: Call CrewAI agents directly - use the run_crew abstraction