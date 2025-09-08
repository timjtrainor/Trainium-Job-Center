# AGENT.md — FastAPI Routes

**Purpose**: HTTP API endpoints for the job posting fit review pipeline.

**Entrypoints**:
- `POST /jobs/fit-review` → synchronous job evaluation with immediate response
- `POST /jobs/fit-review/async` → asynchronous job evaluation with background processing
- `GET /jobs/fit-review/{job_id}` → retrieve results of async evaluation

**Contracts**:
- Input: `JobPosting` model in request body
- Output: `FitReviewResult` model for sync, status dict for async
- Standard HTTP status codes: 200 (success), 500 (server error), 422 (validation error)

**Conventions**:
- Keep route handlers thin; delegate business logic to services
- Use FastAPI dependency injection for shared resources
- Log all requests with correlation IDs for tracing
- Handle errors gracefully with informative error messages
- Use appropriate HTTP methods (POST for creation, GET for retrieval)

**Do/Don't**:
- ✅ Do: Validate input using Pydantic models automatically
- ✅ Do: Use async route handlers for all endpoints
- ✅ Do: Include comprehensive OpenAPI documentation via docstrings
- ✅ Do: Handle exceptions and return appropriate HTTP status codes
- ❌ Don't: Put business logic in route handlers; delegate to services
- ❌ Don't: Return raw exceptions to clients; use HTTPException
- ❌ Don't: Forget to log requests and responses for monitoring