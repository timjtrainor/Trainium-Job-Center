# CrewAI Job Review Service

A multi-agent job analysis system inspired by CrewAI architecture that provides comprehensive evaluation of job postings through specialized AI agents.

## Overview

The CrewAI Job Review Service implements a multi-agent approach where different specialized "agents" analyze various aspects of job postings to provide comprehensive insights, quality scores, and recommendations.

## Performance Features

### Early Termination
The system implements **early termination** logic to improve performance:
- When any persona/agent **rejects** a job posting, processing stops immediately
- This prevents unnecessary computation on clearly unsuitable positions
- Significantly improves response time for rejected jobs
- Maintains full analysis for potentially suitable positions

### Consistent Response Format
All responses follow a standardized format suitable for API responses and database storage:
```json
{
    "status": "success",
    "data": {
        "job_id": "string",
        "correlation_id": null,
        "final": {
            "recommend": boolean,
            "rationale": "string", 
            "confidence": "low|medium|high"
        },
        "personas": [
            {
                "id": "persona_name",
                "recommend": boolean,
                "reason": "string"
            }
        ],
        "tradeoffs": [],
        "actions": ["string"],
        "sources": ["string"]
    },
    "error": null,
    "message": "Job posting analysis completed successfully"
}

## Architecture

### Specialized Agents

#### 1. SkillsAnalysisAgent
**Responsibility**: Analyzes job skills, requirements, experience level, and education requirements.

**Capabilities**:
- Technical skills extraction (Python, Java, React, AWS, etc.)
- Experience level determination (Entry-Level, Mid-Level, Senior)
- Education requirements analysis
- Skills categorization (required vs preferred)

**Output**:
```python
{
    "required_skills": ["Python", "React", "SQL"],
    "preferred_skills": ["AWS", "Docker"],
    "experience_level": "Senior",
    "education_requirements": "Bachelor's Degree"
}
```

#### 2. CompensationAnalysisAgent
**Responsibility**: Analyzes compensation data, salary ranges, and benefits.

**Capabilities**:
- Salary range analysis and competitiveness assessment
- Compensation transparency scoring
- Benefits extraction and categorization
- Market-based salary competitiveness evaluation

**Output**:
```python
{
    "salary_analysis": {
        "has_salary_info": True,
        "min_salary": 140000,
        "max_salary": 180000,
        "estimated_average": 160000,
        "transparency_score": 100,
        "competitiveness": "Competitive"
    },
    "benefits_mentioned": ["health insurance", "401k", "flexible work"]
}
```

#### 3. QualityAssessmentAgent
**Responsibility**: Assesses job posting quality and identifies red/green flags.

**Capabilities**:
- Job posting quality scoring (0-100)
- Description completeness assessment
- Red flag identification (MLM schemes, unrealistic requirements, poor grammar)
- Green flag identification (professional development, benefits, work-life balance)

**Output**:
```python
{
    "job_quality_score": 85.0,
    "description_completeness": 90.0,
    "red_flags": [],
    "green_flags": ["Emphasizes professional development", "Comprehensive job description"]
}
```

## API Endpoints

### POST /jobs/review
Analyze a single job using the multi-agent review system.

**Request Body**:
```json
{
    "title": "Senior Software Engineer",
    "company": "TechCorp Inc",
    "description": "Job description text...",
    "location": "San Francisco, CA",
    "is_remote": false,
    "salary_min": 140000,
    "salary_max": 180000,
    "site": "indeed"
}
```

**Response**:
```json
{
    "success": true,
    "data": {
        "job_id": "job_1234567890",
        "title": "Senior Software Engineer",
        "company": "TechCorp Inc",
        "required_skills": ["Python", "React", "PostgreSQL"],
        "preferred_skills": ["AWS", "Docker", "Kubernetes"],
        "experience_level": "Senior",
        "education_requirements": "Bachelor's Degree",
        "salary_analysis": {
            "has_salary_info": true,
            "competitiveness": "Competitive",
            "transparency_score": 100
        },
        "benefits_mentioned": ["health insurance", "401k", "flexible work"],
        "job_quality_score": 85.0,
        "description_completeness": 90.0,
        "red_flags": [],
        "green_flags": ["Emphasizes professional development"],
        "overall_recommendation": "Recommended",
        "confidence_score": 88.5,
        "analysis_timestamp": "2025-01-02T...",
        "agents_used": ["SkillsAnalysisAgent", "CompensationAnalysisAgent", "QualityAssessmentAgent"]
    }
}
```

### POST /jobs/review/batch
Analyze multiple jobs (up to 50) and return results sorted by recommendation quality.

**Request Body**:
```json
[
    { "title": "Job 1", "company": "Company A", ... },
    { "title": "Job 2", "company": "Company B", ... }
]
```

**Response**:
```json
{
    "success": true,
    "data": {
        "analyses": [...],
        "total_analyzed": 2,
        "highly_recommended": 1,
        "recommended": 1
    }
}
```

### GET /jobs/review/from-db
Analyze jobs from the database with optional filters.

**Query Parameters**:
- `limit` (int, max 50): Number of jobs to analyze
- `site` (string): Filter by job site (indeed, linkedin, etc.)
- `company` (string): Filter by company name (partial match)
- `title_contains` (string): Filter jobs with title containing text

**Example**: `/jobs/review/from-db?limit=10&site=indeed&company=google`

### GET /jobs/review/agents
Get information about available analysis agents and their capabilities.

### GET /jobs/review/health
Health check for the CrewAI job review service.

## Analysis Output Schema

### JobAnalysis Object
```python
{
    "job_id": str,
    "title": str,
    "company": str,
    
    # Skills Analysis
    "required_skills": List[str],
    "preferred_skills": List[str],
    "experience_level": str,  # "Entry-Level" | "Mid-Level" | "Senior" | "Not Specified"
    "education_requirements": str,
    
    # Compensation Analysis
    "salary_analysis": Dict[str, Any],
    "benefits_mentioned": List[str],
    
    # Quality Assessment
    "job_quality_score": float,  # 0-100
    "description_completeness": float,  # 0-100
    "red_flags": List[str],
    "green_flags": List[str],
    
    # Company and Market Analysis
    "company_insights": Dict[str, Any],
    "industry_category": str,
    "remote_work_options": str,
    
    # Overall Assessment
    "overall_recommendation": str,  # "Highly Recommended" | "Recommended" | "Consider with Caution" | "Not Recommended"
    "confidence_score": float,  # 0-100
    
    # Metadata
    "analysis_timestamp": datetime,
    "agents_used": List[str]
}
```

## Quality Scoring

### Job Quality Score (0-100)
- **Basic Information Completeness (40 points)**
  - Title length and clarity (15 points)
  - Company information (10 points)
  - Description length and detail (15 points)

- **Description Quality (40 points)**
  - Comprehensive description >500 chars (10 points)
  - Clear responsibilities section (10 points)
  - Clear requirements section (10 points)
  - Benefits mentioned (10 points)

- **Professional Presentation (20 points)**
  - No suspicious language patterns (10 points)
  - Proper capitalization and formatting (10 points)

### Confidence Score Calculation
Weighted combination of:
- Quality score (40%)
- Description completeness (30%)
- Salary information availability (10%)
- Green vs red flags balance (20%)

## Red Flags Detection

The system identifies potential issues in job postings:

- **Unprofessional Language**: "rockstar", "ninja", "guru", "unicorn"
- **MLM Indicators**: "unlimited earning potential", "be your own boss"
- **Unrealistic Promises**: "make $5000/week", "no experience necessary"
- **Poor Grammar**: Excessive punctuation, unprofessional formatting
- **Unrealistic Requirements**: Entry-level positions requiring 5+ years experience

## Green Flags Detection

Positive indicators that improve job recommendation:

- **Professional Development**: Mentorship, career growth, training opportunities
- **Work-Life Balance**: Flexible hours, remote options, good benefits
- **Comprehensive Information**: Detailed job description, clear requirements
- **Inclusive Language**: Diversity, equal opportunity statements
- **Quality Benefits**: Health insurance, retirement plans, professional development

## Integration

### Database Integration
The service integrates with the existing job database to analyze stored job postings:

```sql
SELECT job_id, site, title, company, description, location, 
       is_remote, min_amount, max_amount, interval
FROM jobs 
WHERE [filters]
ORDER BY created_at DESC
```

### Service Dependencies
- **DatabaseService**: For accessing job data
- **JobPersistenceService**: For understanding job data structure
- **Existing FastAPI patterns**: Follows established error handling and response patterns

## Usage Examples

### Analyze a Single Job
```python
from app.services.crewai import get_job_review_crew

crew = get_job_review_crew().job_review()

job_data = {
    "title": "Software Engineer",
    "company": "Tech Company",
    "description": "We are looking for...",
    # ... other fields
}

analysis = crew.kickoff(inputs={"job": job_data})
print(f"Recommendation: {analysis.overall_recommendation}")
print(f"Quality Score: {analysis.job_quality_score}")
```

### Analyze Multiple Jobs
```python
jobs = [job1_data, job2_data, job3_data]
analyses = await service.analyze_multiple_jobs(jobs)

# Results are sorted by recommendation quality
for analysis in analyses:
    print(f"{analysis.title}: {analysis.overall_recommendation}")
```

### Retrieve Context from Chroma
Agents can pull supplementary information from a Chroma vector collection using CrewAI tools:
```python
from app.services.crewai.tools import get_chroma_search_tool
from crewai import Agent

search_tool = get_chroma_search_tool("jobs")

agent = Agent(
    role="Context seeker",
    goal="Look up related job snippets",
    backstory="Consults the vector store for prior analyses",
    tools=[search_tool],
)

context = agent.run("Find examples of Python developer roles")
print(context)
```

## Performance Characteristics

- **Single Job Analysis**: ~50-100ms per job
- **Batch Processing**: Efficient sequential processing with error isolation
- **Memory Usage**: Minimal, stateless analysis
- **Database Impact**: Read-only queries with configurable limits

## Future Enhancements

1. **Machine Learning Integration**: Train models on analysis patterns
2. **External Data Sources**: Company information APIs, salary databases
3. **Custom Scoring Models**: Industry-specific or role-specific scoring
4. **Real-time Analysis**: WebSocket-based live job analysis
5. **Analytics Dashboard**: Aggregate analysis insights and trends

## Error Handling

The service implements comprehensive error handling:
- Individual job failures don't stop batch processing
- Missing data is handled gracefully with fallback values
- Database connection issues are properly logged and reported
- Malformed input data is validated and rejected with clear error messages

## Logging

Structured logging is implemented throughout:
```json
{
    "timestamp": "2025-01-02T...",
    "service": "CrewAI Job Review",
    "job_id": "job_123",
    "event": "analysis_completed",
    "recommendation": "Recommended",
    "confidence": 85.5
}
```