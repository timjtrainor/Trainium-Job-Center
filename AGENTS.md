# AGENTS Instructions

## General
- Use descriptive commit messages.
- Run `npm run build` after changing frontend code.
- Run `python -m py_compile $(git ls-files '*.py')` after changing Python code.

## Frontend
- Use TypeScript with React and Vite.
- Prefer React Query for data fetching and caching.
- Debounce search inputs and reflect filters in the URL.
- Style with Tailwind CSS or CSS Modules, providing visible focus states and keyboard-friendly modals.
- Make user-visible decisions with UI elements like toasts or badges; avoid relying on console logs.
- Do not invent new backend endpoints; use the ones provided by the API.

## Python Service
- Build FastAPI endpoints with async functions.
- Keep modules organized under `app/api`, `app/schemas`, and `app/services`.
- Reserve `app/models` for future ORM models.

## CrewAI Services
The Python service includes active CrewAI multi-agent services:

### 1. Job Posting Review (`job_posting_review`)
- **Purpose**: Analyzes job postings for fit and alignment with candidate criteria
- **Location**: `python-service/app/services/crewai/job_posting_review/`
- **Agents**: Job Intake, Pre-filter, Quick Fit Analyst, Brand Framework Matcher
- **Usage**: Orchestrated evaluation pipeline with YAML-driven configuration

### 2. Personal Branding (`personal_branding`)
- **Purpose**: Assists with personal brand development and career positioning
- **Location**: `python-service/app/services/crewai/personal_branding/`
- **Usage**: Provides branding guidance and career development insights

### 3. Research Company (`research_company`) 
- **Purpose**: Comprehensive company research and analysis
- **Location**: `python-service/app/services/crewai/research_company/`
- **Usage**: Gathers and analyzes company information for job applications

### 4. LinkedIn Job Search (`linkedin_job_search`)
- **Purpose**: Coordinates LinkedIn job searches and recommendations
- **Location**: `python-service/app/services/crewai/linkedin_job_search/`
- **Process**: Hierarchical with manager agent coordination
- **Usage**: LinkedIn-focused job discovery and networking strategies

All CrewAI services follow YAML-first configuration and modular agent design patterns.

### CrewAI Architecture Requirements
- **Hierarchical Process**: Requires a `manager_agent` parameter in the crew definition to coordinate specialist agents and synthesize outputs
- **Sequential Process**: Agents execute tasks in defined order without requiring a manager agent
- **Manager Agent**: Must have appropriate role, goal, backstory, and tool access to effectively coordinate and synthesize outputs from specialist agents
- **Configuration**: All agent definitions must be properly wired in both `agents.yaml` and `crew.py` files
