# LinkedIn Recommended Jobs Crew

A CrewAI crew for fetching and normalizing LinkedIn job recommendations. This crew is responsible ONLY for data retrieval and normalization - it does NOT perform any recommendation logic, filtering, ranking, or job evaluation.

## Purpose

This crew fetches personalized job recommendations from LinkedIn and normalizes them into a standardized JobPosting schema. It serves as a data retrieval layer that other crews can use for analysis and recommendations.

## Workflow

1. **Job Collection**: Uses the MCP Gateway LinkedIn tool `get_recommended_jobs` to fetch all personalized job recommendations for the logged-in LinkedIn user
2. **Job Details Retrieval**: For each job returned, calls the MCP Gateway LinkedIn tool `get_job_details` to retrieve the full job posting information
3. **Data Normalization**: Transforms raw LinkedIn data into standardized JobPosting objects
4. **Documentation Updates**: Updates project documentation to reflect current crew functionality

## Agents

### Job Collector Agent
- **Role**: LinkedIn Job Collector
- **Goal**: Use the get_recommended_jobs tool to fetch recommended job IDs for the current user
- **Backstory**: An efficient LinkedIn researcher who knows how to surface personalized recommendations without interpreting or analyzing them

### Job Details Agent  
- **Role**: LinkedIn Job Details Fetcher
- **Goal**: For each job ID provided by the collector, call get_job_details and return normalized JobPosting objects
- **Backstory**: A detail-driven analyst who ensures job postings are accurately captured, not interpreted

### Documentation Agent
- **Role**: Project Documentation Maintainer
- **Goal**: Ensure README.md or other relevant documentation reflects the crew's function, tasks, and output schema
- **Backstory**: A meticulous writer who keeps technical docs aligned with system behavior

## Tasks

### Collect Recommended Jobs Task
- **Description**: Call get_recommended_jobs to fetch LinkedIn job recommendations. Extract the job IDs.
- **Expected Output**: A JSON array of job IDs with metadata
- **Agent**: Job Collector Agent

### Fetch Job Details Task
- **Description**: For each job ID collected, call get_job_details. Map response fields into JobPosting schema.
- **Expected Output**: A JSON array of JobPosting objects
- **Agent**: Job Details Agent
- **Context**: Requires output from Collect Recommended Jobs Task

### Update Documentation Task
- **Description**: Review and update project documentation to reflect the crew's purpose and output schema
- **Expected Output**: Updated documentation reflecting current crew design
- **Agent**: Documentation Agent
- **Context**: Requires output from both previous tasks

## Output Schema

The crew produces a JSON array of JobPosting objects with the following exact structure:

```json
[
  {
    "title": "Job Title",
    "company": "Company Name",
    "location": "Job Location", 
    "description": "Full job description text",
    "url": "https://linkedin.com/jobs/view/job_id"
  }
]
```

### Required Fields
- **title** (string): Job title
- **company** (string): Company name
- **location** (string): Job location
- **description** (string): Full job description
- **url** (string): Valid URI to the job posting (1-2083 characters)

## Crew Configuration

- **Execution**: Sequential (Collector → Details → Documentation)
- **Process**: `Process.sequential` - tasks execute in defined order
- **Configuration**: Agents and tasks defined in YAML (`agents.yaml` and `tasks.yaml`)
- **MCP Integration**: Uses LinkedIn MCP tools through the MCP Gateway

## MCP Tools Required

- **get_recommended_jobs**: Fetches personalized job recommendations for the current user
- **get_job_details**: Retrieves detailed information for a specific job ID

## Usage

```python
from app.services.crewai.linkedin_recommended_jobs import run_linkedin_recommended_jobs

# Execute the crew workflow
result = run_linkedin_recommended_jobs()

# Access the normalized job postings
job_postings = result.get('data', [])
```

## Important Constraints

⚠️ **This crew does NOT include any recommendation, ranking, or filtering logic**

- No job fit analysis
- No quality scoring
- No applicant matching
- No preference filtering
- Strictly data retrieval and normalization only

Other crews in the system handle analysis and recommendations based on this crew's output.

## Integration Notes

- Designed to work with the existing MCP Gateway infrastructure
- Follows established CrewAI patterns from other crews in the system
- Can be used as input for other analysis crews (job_posting_review, etc.)
- Maintains separation of concerns: data retrieval vs. data analysis