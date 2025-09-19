# LinkedIn Job Search Crews

This document describes the implementation of two LinkedIn job search CrewAI crews that provide different approaches to job discovery.

## Overview

The LinkedIn Job Search implementation consists of two complementary crews:

1. **Crew A: Parameterized LinkedIn Search** - Execute explicit user-defined LinkedIn searches
2. **Crew B: Brand-Driven Autonomous Search** - Generate searches automatically from career brand data

Both crews integrate with the existing `jobs` database table and follow established CrewAI patterns.

## Crew A: Parameterized LinkedIn Search

### Purpose
Execute LinkedIn job searches with explicit user-defined inputs and retrieve personalized recommendations.

### Architecture
- **search_agent**: Calls LinkedIn MCP `search_jobs` with provided parameters
- **recommendation_agent**: Calls LinkedIn MCP `get_recommended_jobs` for authenticated users
- **orchestration_agent**: Consolidates and deduplicates results from both agents

### API Endpoint
```http
POST /crewai/linkedin-job-search/search
```

### Request Example
```json
{
  "keywords": "senior software engineer",
  "location": "San Francisco, CA",
  "job_type": "full-time",
  "date_posted": "past-week",
  "experience_level": "senior",
  "remote": true,
  "limit": 25
}
```

### Response Format
```json
{
  "success": true,
  "data": {
    "consolidated_jobs": [
      {
        "title": "Senior Software Engineer",
        "company": "TechCorp",
        "location": "San Francisco, CA",
        "job_type": "full-time",
        "job_url": "https://linkedin.com/jobs/123456",
        "site": "linkedin",
        "is_remote": true,
        "description": "Job description..."
      }
    ],
    "total_jobs": 25,
    "search_jobs_count": 20,
    "recommended_jobs_count": 8,
    "duplicates_removed": 3
  }
}
```

## Crew B: Brand-Driven Autonomous Search

### Purpose
Derive search queries automatically from the candidate's career brand collection in ChromaDB and score results for brand alignment.

### Architecture
- **brand_query_generator**: Extracts career brand data and generates targeted search queries
- **linkedin_search_executor**: Executes LinkedIn searches using brand-derived queries
- **brand_alignment_scorer**: Scores job results against brand dimensions
- **orchestration_manager**: Compiles final prioritized results

### Brand Dimensions
The system analyzes five career brand dimensions:
1. **North Star & Vision** - Leadership and strategic roles
2. **Trajectory & Mastery** - Skill-based and growth opportunities
3. **Values Compass** - Culture and mission alignment
4. **Lifestyle Alignment** - Work-life balance and location preferences
5. **Compensation Philosophy** - Role level and compensation expectations

### API Endpoints

#### Execute Brand-Driven Search
```http
POST /crewai/brand-driven-job-search/search
```

Request:
```json
{
  "user_id": "user_123",
  "limit_per_section": 10
}
```

#### Check Brand Data Status
```http
GET /crewai/brand-driven-job-search/status/{user_id}
```

#### Preview Generated Queries
```http
GET /crewai/brand-driven-job-search/brand-queries/{user_id}
```

### Response Format
```json
{
  "success": true,
  "data": {
    "brand_driven_jobs": [
      {
        "title": "Senior Engineering Manager",
        "company": "TechCorp",
        "location": "Remote",
        "job_url": "https://linkedin.com/jobs/123456",
        "brand_metadata": {
          "originating_section": "north_star_vision",
          "search_keywords": "leadership strategy vision",
          "overall_brand_score": 84,
          "priority": "high",
          "brand_alignments": {
            "north_star_vision": 90,
            "trajectory_mastery": 82,
            "values_compass": 78,
            "lifestyle_alignment": 85,
            "compensation_philosophy": 88
          }
        }
      }
    ],
    "execution_summary": {
      "total_jobs_found": 45,
      "brand_sections_queried": 5,
      "successful_searches": 4,
      "high_priority_jobs": 12,
      "autonomous_search_success": true
    },
    "brand_insights": {
      "most_productive_section": "trajectory_mastery",
      "best_aligned_opportunities": 12
    }
  }
}
```

## Database Integration

Both crews store results in the existing `jobs` table:

- **Standard fields**: `title`, `company`, `location`, `job_type`, `job_url`, `site`, `is_remote`, `description`
- **Brand metadata**: Stored in `source_raw` JSONB field for brand-driven results
- **Deduplication**: Uses existing `(site, job_url)` unique constraint

### Brand Metadata Schema
```json
{
  "brand_metadata": {
    "originating_section": "north_star_vision",
    "search_keywords": "leadership strategy vision",
    "overall_brand_score": 84,
    "priority": "high",
    "brand_alignments": {
      "north_star_vision": 90,
      "trajectory_mastery": 82,
      "values_compass": 78,
      "lifestyle_alignment": 85,
      "compensation_philosophy": 88
    }
  },
  "crew_type": "brand_driven_job_search",
  "search_timestamp": "2024-01-15T10:30:00Z"
}
```

## Error Handling

Both crews implement comprehensive error handling:

### LinkedIn API Limitations
- Rate limit detection and graceful degradation
- Authentication status checking for recommendations
- Partial failure handling (e.g., search succeeds but recommendations fail)

### Brand Data Requirements
- ChromaDB connection validation
- Brand data existence checking
- Fallback for missing brand sections

### Example Error Responses
```json
{
  "success": false,
  "error": "LinkedIn job search failed",
  "message": "LinkedIn API rate limit exceeded. Please try again later."
}
```

## Usage Examples

### Parameterized Search
```python
from app.services.crewai.linkedin_job_search.crew import run_linkedin_job_search

result = run_linkedin_job_search(
    keywords="data scientist",
    location="Remote",
    remote=True,
    limit=20
)
```

### Brand-Driven Search
```python
from app.services.crewai.brand_driven_job_search.crew import run_brand_driven_job_search

result = run_brand_driven_job_search(user_id="user_123")
```

## Health Monitoring

Both crews provide health check endpoints:

- `/crewai/linkedin-job-search/health`
- `/crewai/brand-driven-job-search/health`

Health checks verify:
- Crew initialization
- MCP tool availability
- Agent and task configuration
- ChromaDB connectivity (brand-driven crew)

## Testing

Comprehensive test suites are provided:

- **Unit tests**: `tests/services/test_*_crew.py`
- **API tests**: `tests/api/test_*_api.py`
- **Mock mode**: Set `CREWAI_MOCK_MODE=true` for testing without external dependencies

## Configuration

Both crews use YAML-first configuration following established patterns:

- **Agents**: `config/agents.yaml` - Defines agent roles, goals, and tools
- **Tasks**: `config/tasks.yaml` - Defines task descriptions and expected outputs
- **Environment**: MCP tools loaded via environment configuration

## Future Enhancements

1. **Advanced Scoring**: Machine learning models for brand alignment
2. **Company Intelligence**: Integration with company research crew
3. **Application Tracking**: Direct integration with application management
4. **Notification System**: Real-time alerts for high-priority matches
5. **Learning System**: Feedback loops to improve search query generation