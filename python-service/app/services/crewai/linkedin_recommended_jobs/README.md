# LinkedIn Recommended Jobs Crew

A CrewAI crew for fetching and normalizing LinkedIn job recommendations. This crew is responsible ONLY for data retrieval and normalization - it does NOT perform any recommendation logic, filtering, ranking, or job evaluation.

## Purpose

This crew fetches personalized job recommendations from LinkedIn and normalizes them into a standardized JobPosting schema. It serves as a data retrieval layer that other crews can use for analysis and recommendations.

## Workflow

1. **Job Collection**: Uses MCP tools to fetch all personalized job recommendations for the logged-in LinkedIn user
2. **Job Details Retrieval**: For each job returned, retrieves the full job posting information  
3. **Data Normalization**: Transforms raw LinkedIn data into standardized JobPosting objects
4. **Documentation Updates**: Updates project documentation to reflect current crew functionality

## MCP Integration

This crew uses the **simplified MCP integration approach** with `MCPServerAdapter` from `crewai_tools`:

```python
from crewai_tools import MCPServerAdapter

# Simple configuration pointing to MCP Gateway
server_configurations = [
    {
        "url": "http://localhost:8811/mcp", 
        "transport": "streamable-http"
    }
]

with MCPServerAdapter(server_configurations) as tools:
    # Tools are automatically available to agents
    print("Available MCP Tools:", [tool.name for tool in tools])
```

This approach is much simpler than the complex MCP factory system and directly leverages CrewAI's native MCP support.

## Agents

### Job Collector Agent
- **Role**: LinkedIn Job Collector
- **Goal**: Use MCP tools to fetch recommended job IDs for the current user
- **Tools**: LinkedIn MCP tools (filtered automatically)
- **Backstory**: An efficient LinkedIn researcher who knows how to surface personalized recommendations

### Job Details Agent  
- **Role**: LinkedIn Job Details Fetcher
- **Goal**: For each job ID, retrieve full job posting data and normalize to JobPosting schema
- **Tools**: LinkedIn MCP tools (filtered automatically)
- **Backstory**: A detail-driven analyst who ensures job postings are accurately captured

### Documentation Agent
- **Role**: Project Documentation Maintainer
- **Goal**: Ensure README.md reflects the crew's function, tasks, and output schema
- **Tools**: None (documentation-focused)
- **Backstory**: A meticulous writer who keeps technical docs aligned with system behavior

## Tasks

### Collect Recommended Jobs Task
- **Description**: Use MCP tools to fetch LinkedIn job recommendations and extract job IDs
- **Expected Output**: A JSON array of job IDs with metadata
- **Agent**: Job Collector Agent

### Fetch Job Details Task
- **Description**: For each job ID, retrieve full job posting data and normalize to JobPosting schema
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
- **MCP Integration**: Uses `MCPServerAdapter` from `crewai_tools` (simplified approach)

## MCP Gateway Connection

- **Gateway URL**: `http://localhost:8811/mcp`
- **Transport**: `streamable-http`
- **Tools**: LinkedIn MCP tools (auto-filtered by name matching)
- **Cleanup**: Automatic cleanup via `__del__` method

## MCP Tools Required

- LinkedIn MCP tools (automatically discovered and filtered)

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

- **Simplified MCP**: Uses `MCPServerAdapter` directly instead of complex factory system
- **Native CrewAI**: Leverages CrewAI's built-in MCP support
- **Gateway Integration**: Connects to existing MCP Gateway Docker service
- **Tool Filtering**: Automatically filters LinkedIn-specific tools
- **YAML Configuration**: Maintains YAML approach for agents and tasks as requested
- **Separation of Concerns**: Clean separation between data retrieval and analysis