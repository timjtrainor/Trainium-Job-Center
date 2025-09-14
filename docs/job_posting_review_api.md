# Job Posting Review CrewAI API

This document describes the production-ready HTTP API for the job posting review CrewAI functionality.

## Overview

The job posting review system uses CrewAI to orchestrate multiple AI agents that analyze job postings and provide structured recommendations. The system follows a hierarchical process with a managing agent controlling the workflow.

## API Endpoints

### POST /crewai/job-posting-review/analyze

Analyze a job posting using the full CrewAI workflow.

**Request Body:**
```json
{
  "job_posting": {
    "title": "Senior Machine Learning Engineer",
    "company": "Acme Corp", 
    "description": "We are looking for a senior ML engineer...",
    "location": "San Francisco, CA",
    "salary": "$180,000 - $220,000"
  },
  "options": {
    "detailed_analysis": true,
    "include_market_research": false
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "job_id": "job_a1b2c3d4",
    "final": {
      "recommend": true,
      "rationale": "Strong technical fit with excellent growth opportunities...",
      "confidence": "high"
    },
    "personas": [
      {
        "id": "job_posting_review_crew",
        "recommend": true,
        "reason": "Analyzed by job posting review crew with hierarchical orchestration"
      }
    ],
    "tradeoffs": [],
    "actions": [],
    "sources": ["job_posting_review_crew", "crewai_orchestration"]
  },
  "message": "Job posting analysis completed successfully"
}
```

### POST /crewai/job-posting-review/analyze/simple

Simplified endpoint for basic job posting analysis.

**Request Body:**
```json
"Senior Software Engineer at Google, $200k salary, remote work available"
```

**Response:**
```json
{
  "status": "success", 
  "data": {
    "result": "Analysis completed successfully with recommendation...",
    "crew_output": true
  },
  "message": "Job posting analysis completed successfully"
}
```

### GET /crewai/job-posting-review/health

Health check endpoint for the service.

**Response:**
```json
{
  "status": "success",
  "data": {
    "service": "JobPostingReviewCrew",
    "agents_count": 5,
    "tasks_count": 5,
    "process": "Process.hierarchical",
    "agents": [
      {
        "role": "Job Intake Agent",
        "goal": "Extract structured data from raw job postings",
        "tools_count": 0
      }
    ],
    "tasks": [
      {
        "description": "Parse job_posting into structured JSON...",
        "agent_role": "Job Intake Agent"
      }
    ],
    "status": "healthy"
  },
  "message": "Job posting review service is healthy"
}
```

### GET /crewai/job-posting-review/config

Get detailed configuration information about the crew.

**Response:**
```json
{
  "status": "success",
  "data": {
    "crew_type": "JobPostingReviewCrew",
    "process_type": "Process.hierarchical", 
    "agent_roles": [
      "Job Intake Agent",
      "Job Pre-Filter Agent", 
      "Quick Fit Analyst",
      "Career Brand Matcher",
      "Job Screening Orchestrator"
    ],
    "task_flow": [
      {
        "task_id": 0,
        "description": "Parse job_posting into structured JSON...",
        "agent": "Job Intake Agent"
      }
    ],
    "workflow_description": "1. Job Intake Agent: Parse job posting into structured JSON..."
  },
  "message": "Crew configuration retrieved successfully"
}
```

## CrewAI Workflow

The system uses a 5-agent hierarchical workflow:

### 1. Job Intake Agent
- **Role**: Extract structured data from raw job postings
- **Output**: Clean JSON object with job attributes

### 2. Pre-Filter Agent  
- **Role**: Apply hard rejection rules (salary, seniority, location)
- **Output**: "reject" with reason or "pass" to continue
- **Rules**: 
  - Reject if salary < $180k/year
  - Reject if no salary AND seniority < Senior
  - Reject if salary < $210k/year AND location is in-person

### 3. Quick Fit Analyst
- **Role**: Score career growth, compensation, lifestyle fit, purpose alignment
- **Output**: JSON with scores (0-10) and recommendation
- **Tools**: ChromaDB search for career framework data

### 4. Brand Framework Matcher
- **Role**: Compare against user's career brand framework
- **Output**: Similarity scores and alignment notes  
- **Tools**: ChromaDB search for brand framework data

### 5. Managing Agent (Orchestrator)
- **Role**: Control the workflow and provide final recommendation
- **Process**: 
  1. Run intake → pre-filter
  2. If rejected, stop
  3. If passed, run quick fit analysis
  4. If "review_deeper" recommended, run brand matching
  5. Provide final decision

## Integration Notes

### Existing API Compatibility

The system maintains compatibility with the existing `/jobs/posting/fit_review` endpoint by providing a `run_crew()` function that returns data in the expected `FitReviewResult` format.

### Error Handling

All endpoints use the `StandardResponse` format and handle errors gracefully:

```json
{
  "status": "error",
  "error": "Job posting analysis failed", 
  "message": "Detailed error message here"
}
```

### Dependencies

- **FastAPI**: Web framework
- **CrewAI**: Multi-agent orchestration
- **ChromaDB**: Vector database for career framework data
- **Pydantic**: Data validation and serialization
- **loguru**: Structured logging

## Configuration Files

### agents.yaml
Defines the 5 agents with their roles, goals, backstories, and tool assignments.

### tasks.yaml  
Defines the 5 tasks with descriptions, expected outputs, and agent assignments.

## Testing

Use the provided test files:
- `tests/api/test_job_posting_review.py` - API endpoint tests
- `manual_crew_test.py` - Manual verification script

## Usage Examples

### Basic Analysis
```bash
curl -X POST "http://localhost:8000/crewai/job-posting-review/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "job_posting": "Senior Python Developer at TechCorp, $190k, remote"
  }'
```

### Detailed Analysis with Options
```bash  
curl -X POST "http://localhost:8000/crewai/job-posting-review/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "job_posting": {
      "title": "Senior ML Engineer",
      "company": "AI Startup",
      "salary": "$200,000 - $250,000", 
      "location": "Remote",
      "description": "Full job description here..."
    },
    "options": {
      "detailed_analysis": true
    }
  }'
```