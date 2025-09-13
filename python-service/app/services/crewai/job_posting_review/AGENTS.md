# Job Posting Review Crew - AGENTS.md

## Purpose

The Job Posting Review Crew provides comprehensive evaluation of job opportunities against the user's career brand framework, incorporating company research data to deliver personalized fit assessments across multiple dimensions: skills alignment, cultural fit, compensation competitiveness, and career growth potential.

## Roles and Goals of Each Agent

### Skills Analyst
- **Role**: Skills and Requirements Analyst
- **Goal**: Evaluate how well the candidate's skills and experience align with the job requirements
- **Responsibilities**:
  - Analyze technical and soft skill requirements vs candidate capabilities
  - Assess experience levels and seniority match
  - Identify skill gaps and development opportunities
  - Leverage ChromaDB career brand data for candidate skills context

### Culture Analyst
- **Role**: Cultural Fit and Alignment Analyst  
- **Goal**: Assess alignment between company culture, values, and the candidate's preferences
- **Responsibilities**:
  - Analyze company values alignment with candidate values
  - Evaluate work environment and team dynamics
  - Assess management style and organizational structure compatibility
  - Consider work-life balance and flexibility factors
  - Leverage ChromaDB career brand data for cultural preferences

### Compensation Analyst
- **Role**: Compensation and Benefits Analyst
- **Goal**: Evaluate the competitiveness of compensation, benefits, and total rewards package
- **Responsibilities**:
  - Research current market compensation data via web search tools
  - Analyze salary ranges, equity, and benefits packages  
  - Evaluate total compensation competitiveness
  - Consider location and experience level factors
  - Assess growth potential in compensation

### Career Trajectory Analyst
- **Role**: Career Growth and Trajectory Analyst
- **Goal**: Analyze career advancement opportunities and alignment with long-term career goals
- **Responsibilities**:
  - Evaluate advancement and leadership opportunities
  - Assess skill development and learning support
  - Analyze industry positioning and market growth
  - Leverage ChromaDB career brand data for trajectory goals
  - Consider long-term career strategy alignment

### Fit Evaluator (Manager Agent)
- **Role**: Job Fit Evaluation Manager
- **Goal**: Synthesize all analyses into a comprehensive fit evaluation and recommendation
- **Responsibilities**:
  - Integrate findings from all specialist agents
  - Provide overall recommendation with clear rationale
  - Identify key strengths, concerns, and decision factors
  - Generate actionable recommendations and negotiation points
  - Coordinate and manage the analysis workflow

## Task Flow and Dependencies

### Sequential Task Execution (Hierarchical Process)

1. **Parallel Specialist Analysis Phase**:
   - Skills Analysis Task (async)
   - Culture Analysis Task (async)  
   - Compensation Analysis Task (async)
   - Career Trajectory Analysis Task (async)

2. **Synthesis Phase**:
   - Fit Evaluation Task (depends on all specialist analyses)

### Task Dependencies
- All specialist tasks run in parallel to maximize efficiency
- Fit Evaluation Task receives context from all four specialist analyses
- Manager agent (Fit Evaluator) coordinates final synthesis

## Shared Tools Usage

### ChromaDB Search Tool
- **Purpose**: Access career brand framework data stored in ChromaDB
- **Usage**: 
  - Skills Analyst: Retrieve candidate skills and technical background
  - Culture Analyst: Access candidate values and cultural preferences  
  - Career Trajectory Analyst: Understand career goals and aspirations
- **Collection**: `career_brand` with 3 results per query
- **Integration**: Automatic via ChromaSearchTool configuration

### DuckDuckGo Web Search Tools
- **Purpose**: Research current market data and company information
- **Usage**:
  - Compensation Analyst: Gather market salary and benefits data
  - All agents: Access recent company information and industry trends
- **Integration**: Via MCP tools from base utilities

## Input Requirements

### Required Inputs
```python
{
    "job_title": str,           # Job title to analyze
    "company_name": str,        # Company name  
    "job_location": str,        # Job location (optional)
    "job_description": str,     # Full job description text
    "company_research": dict,   # Research data from research_company crew
    "options": dict            # Additional analysis options
}
```

### Company Research Integration
The crew expects company research data from the `research_company` crew, including:
- Financial health and stability analysis
- Workplace culture and employee experience
- Leadership and reputation analysis
- Career growth opportunities within the company

## Output Schema

### Comprehensive Fit Analysis
```json
{
  "job_title": "...",
  "company_name": "...",
  "skills_fit": {
    "technical_alignment": "...",
    "experience_match": "...",
    "skill_gaps": ["..."],
    "strengths": ["..."],
    "skills_score": "...",
    "key_insights": ["..."]
  },
  "cultural_fit": {
    "values_alignment": "...",
    "work_environment": "...",
    "culture_score": "...",
    "cultural_highlights": ["..."],
    "potential_concerns": ["..."]
  },
  "compensation_fit": {
    "market_competitiveness": "...",
    "total_compensation": "...",
    "compensation_score": "...",
    "market_insights": ["..."]
  },
  "career_growth": {
    "advancement_opportunities": "...",
    "trajectory_alignment": "...", 
    "growth_score": "...",
    "career_highlights": ["..."]
  },
  "overall_evaluation": {
    "recommend": true/false,
    "fit_score": "...",
    "confidence_level": "...",
    "rationale": "...",
    "key_strengths": ["..."],
    "key_concerns": ["..."]
  },
  "recommended_actions": ["..."],
  "questions_to_ask": ["..."],
  "negotiation_points": ["..."]
}
```

## FastAPI Integration

### Endpoint
- **URL**: `POST /job-posting-review`
- **Purpose**: Analyze job posting fit against career brand framework
- **Request Schema**: `JobPostingReviewRequest`
- **Response Schema**: `JobPostingReviewResponse`

### Request Format
```python
{
  "job_posting": {
    "title": "Senior Software Engineer",
    "company": "TechCorp", 
    "location": "San Francisco, CA",
    "description": "...",
    "url": "https://...",
    "salary_range": "$120k-160k"
  },
  "company_research": {
    # Data from research_company crew
  },
  "options": {
    # Additional analysis parameters
  }
}
```

### Health Check
- **URL**: `GET /job-posting-review/health`
- **Purpose**: Verify crew initialization and service health

## Maintenance Instructions

### Configuration Updates
1. **Agent Modifications**: Update `config/agents.yaml` for agent role, goal, or backstory changes
2. **Task Changes**: Modify `config/tasks.yaml` for task descriptions or expected outputs
3. **Tool Integration**: Add new tools to agent configurations in YAML files
4. **Schema Updates**: Update Pydantic schemas in `app/schemas/job_posting_review.py`

### Dependencies
- **ChromaDB**: Requires `career_brand` collection with user's career framework data
- **Company Research**: Integrates with `research_company` crew output
- **Web Search**: Uses DuckDuckGo tools for market research
- **LLM Models**: Configured for OpenAI GPT-5-mini and Gemini 2.5-flash

### Testing
- **Unit Tests**: Test individual agent functionality and task execution
- **Integration Tests**: Verify FastAPI endpoint and complete workflow
- **Mock Mode**: Enable `CREWAI_MOCK_MODE=true` for testing without external APIs

### Performance Considerations
- Specialist tasks run in parallel for efficiency
- ChromaDB queries limited to 3 results per agent
- Web search queries optimized for relevant market data
- Hierarchical process ensures proper task coordination

### Error Handling
- Graceful degradation if ChromaDB or web search fails
- Comprehensive error logging with correlation IDs  
- Fallback responses for failed specialist analyses
- Input validation via Pydantic schemas

## Architecture Alignment

This crew follows the standardized CrewAI architecture patterns established in the main AGENTS.md:
- ✅ Standard file structure (crew.py, config/agents.yaml, config/tasks.yaml)
- ✅ CrewAI decorators (@agent, @task, @crew)
- ✅ Hierarchical process with manager agent coordination
- ✅ Proper task delegation and context flow
- ✅ ChromaDB and MCP tools integration
- ✅ FastAPI endpoint with Pydantic schemas
- ✅ Singleton pattern for crew instances
- ✅ Comprehensive error handling and logging