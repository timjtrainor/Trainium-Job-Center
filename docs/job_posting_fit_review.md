# Job Posting Fit Review Pipeline

## Overview

The Job Posting Fit Review pipeline is a CrewAI-powered system that evaluates job postings from multiple perspectives to provide comprehensive fit assessments. The system uses specialized persona agents to analyze different aspects of job opportunities and aggregates their verdicts into actionable recommendations.

## Architecture

### Core Components

- **Orchestrator** (`app/services/fit_review/orchestrator.py`): Coordinates the entire review process
- **Judge** (`app/services/fit_review/judge.py`): Aggregates persona verdicts into final decisions
- **Retrieval** (`app/services/fit_review/retrieval.py`): Handles data preprocessing and normalization
- **Helper Agents** (`app/services/fit_review/helpers/`): Specialized persona evaluators

### Data Flow

1. **Input**: JobPosting model with title, company, location, description, and URL
2. **Preprocessing**: Job description normalization and company context retrieval
3. **Evaluation**: Parallel execution of persona helper agents
4. **Aggregation**: Judge combines verdicts using configured weights and guardrails
5. **Output**: FitReviewResult with recommendation, rationale, and supporting data

## Persona Helpers

### Data Analyst (`data_analyst.py`)
- **Focus**: Data infrastructure, analytics tools, quantitative aspects
- **Decision Lens**: Will this role advance my data science capabilities?

### Strategist (`strategist.py`)
- **Focus**: Long-term career trajectory, industry growth, strategic positioning
- **Decision Lens**: Does this align with my strategic career goals?

### Stakeholder (`stakeholder.py`)
- **Focus**: Collaboration, partnerships, cross-functional work
- **Decision Lens**: Would I want this person as a partner?

### Technical Leader (`technical_leader.py`)
- **Focus**: Engineering excellence, team leadership, technical challenges
- **Decision Lens**: Can this person help us ship sustainably?

### Recruiter (`recruiter.py`)
- **Focus**: Job posting quality, market competitiveness, candidate attractiveness
- **Decision Lens**: Is this a well-structured, attractive opportunity?

### Skeptic (`skeptic.py`)
- **Focus**: Risk assessment, red flags, potential concerns
- **Decision Lens**: What could go wrong with this opportunity?

### Optimizer (`optimizer.py`)
- **Focus**: Career advancement, skill development, opportunity maximization
- **Decision Lens**: How can I maximize value from this role?

## Configuration

### Weights (`config/weights_guardrails.yml`)

Default persona weights for aggregation:
- Builder: 30% (technical implementers)
- Maximizer: 20% (growth optimizers)
- Harmonizer: 20% (team/culture)
- Pathfinder: 15% (strategic navigators)
- Adventurer: 15% (risk-takers)

### Guardrails

- **comp_floor_enforced**: Enforce minimum compensation requirements
- **severe_redflags_block**: Auto-reject jobs with critical issues
- **tie_bias**: Default action when personas are split ("do_not_pursue")
- **min_confidence_threshold**: Minimum confidence for positive recommendations
- **max_red_flags**: Maximum allowed red flags before auto-rejection

## API Endpoints

### Synchronous Evaluation
```
POST /jobs/fit-review
```
Evaluates a job posting and returns complete results immediately.

### Asynchronous Evaluation
```
POST /jobs/fit-review/async
```
Starts evaluation in background, returns job ID for tracking.

```
GET /jobs/fit-review/{job_id}
```
Retrieves results of asynchronous evaluation.

## Data Models

### Input: JobPosting
```python
{
    "title": "Senior Python Developer",
    "company": "Tech Innovations Inc", 
    "location": "San Francisco, CA",
    "description": "We are looking for...",
    "url": "https://example.com/jobs/123"
}
```

### Output: FitReviewResult
```python
{
    "job_id": "job_123",
    "final": {
        "recommend": true,
        "rationale": "Strong technical fit with growth potential",
        "confidence": "high"
    },
    "personas": [...],
    "tradeoffs": ["Compensation vs opportunity"],
    "actions": ["Negotiate salary", "Clarify equity"],
    "sources": ["company_website", "glassdoor"]
}
```

## Usage Examples

### Basic Evaluation
```python
from app.models.job_posting import JobPosting
from app.services.fit_review import FitReviewOrchestrator

job = JobPosting(
    title="Senior Engineer",
    company="StartupCorp",
    location="Remote",
    description="Join our growing team...",
    url="https://jobs.example.com/123"
)

orchestrator = FitReviewOrchestrator()
result = await orchestrator.run(job)

print(f"Recommendation: {result.final.recommend}")
print(f"Confidence: {result.final.confidence}")
```

### Custom Configuration
```python
options = {
    "weights": {
        "technical_leader": 0.4,
        "strategist": 0.3,
        "skeptic": 0.3
    },
    "guardrails": {
        "tie_bias": "pursue"
    }
}

result = await orchestrator.run(job, options)
```

## Testing

The system includes unit tests for all models and components:

```bash
# Run model tests
python -m pytest tests/models/test_fit_review_models.py

# Run service tests  
python -m pytest tests/services/test_fit_review.py

# Run integration tests
python -m pytest tests/integration/test_fit_review_pipeline.py
```

## Monitoring and Logging

All components use structured logging with correlation IDs:
- Request/response logging in routes
- Decision rationale logging in judge
- Persona evaluation logging in helpers
- Error handling with detailed context

## Future Enhancements

- Machine learning integration for weight optimization
- Real-time company data integration
- Historical decision tracking and analysis
- A/B testing framework for persona variations
- Integration with external job boards and ATS systems