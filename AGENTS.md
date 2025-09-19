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

## MCP (Model Context Protocol) Integration

The Python service integrates with MCP servers through the Docker MCP Gateway, providing external tools and data sources to CrewAI agents.

### Architecture Pattern
- **Use Docker MCP Toolkit**: All MCP servers should be integrated through the Docker MCP Toolkit (`docker/mcp-gateway`) following the established pattern with DuckDuckGo.
- **Dynamic Tool Discovery**: MCP tools are discovered dynamically from the gateway at runtime. Do not hard-code tool definitions in application code.
- **Configuration-Driven**: Server configurations are defined in `python-service/mcp-config/servers.json`.
- **Gateway Orchestration**: The MCP Gateway manages server lifecycles and provides a unified API endpoint.

### Implementation Guidelines
1. **Add MCP servers** to the `--servers` parameter in `docker-compose.yml` mcp-gateway service
2. **Register server configurations** in `mcp-config/servers.json` with appropriate Docker commands and environment variables
3. **Tools are loaded automatically** by `MCPServerAdapter` through dynamic discovery from the gateway
4. **Do not modify** `mcp_adapter.py` for new servers - tools should be discovered at runtime

### Available MCP Servers
- **DuckDuckGo** (`mcp/duckduckgo`): Web search capabilities
- **LinkedIn** (`stickerdaniel/linkedin-mcp-server`): LinkedIn people and job search capabilities

### Implementation Requirements
- **When a service is available in the toolkit** (DuckDuckGo, LinkedIn, etc.), it **must** be implemented via the Docker MCP Toolkit for consistency
- **Only if a service is not supported** in the toolkit should standalone integration be considered
- Check [Docker MCP Toolkit](https://hub.docker.com/u/mcp) for available official servers

### Exception Handling
Some MCP services may not yet be available in the Docker MCP Toolkit. In such cases:
- Document the limitation and rationale for alternative approaches
- Consider contributing to the MCP ecosystem or requesting official server creation
- Maintain consistency with the established pattern where possible

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
