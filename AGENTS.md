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

## MCP (Model Context Protocol) Integration

The Python service integrates with MCP servers through the Docker MCP Gateway, providing external tools and data sources to CrewAI agents.

### Architecture Pattern
- **Use Docker MCP Gateway**: All MCP servers are integrated through the Docker MCP Gateway (`mcp-gateway` service in docker-compose.yml) following the established pattern.
- **Dynamic Tool Discovery**: MCP tools are discovered dynamically from the gateway at runtime using `MCPServerAdapter` from `crewai-tools`.
- **Configuration-Driven**: Tools are assigned to agents via YAML configuration files (`config/tools.yaml`).
- **Gateway Orchestration**: The MCP Gateway manages server lifecycles and provides a unified API endpoint.

### Implementation Guidelines
1. **MCP servers are configured** in the `--servers` parameter in `docker-compose.yml` mcp-gateway service
2. **Tools are loaded automatically** by `MCPServerAdapter` through dynamic discovery from the gateway
3. **Agent tool assignment** is done via `config/tools.yaml` files in each crew directory
4. **Follow the established pattern** used in `linkedin_recommended_jobs` crew for consistency

### Available MCP Servers
- **DuckDuckGo** (`mcp/duckduckgo`): Web search capabilities via `duckduckgo_search` and `duckduckgo_news` tools
- **LinkedIn** (`stickerdaniel/linkedin-mcp-server`): LinkedIn people and job search capabilities via tools like `search_jobs`, `get_job_details`, `get_company_profile`, etc.

### Adding New MCP Tools

To add a new MCP server or tools to an existing crew:

1. **Add the MCP server** to docker-compose.yml `mcp-gateway` service `--servers` parameter:
   ```yaml
   command:
     - --servers=duckduckgo,linkedin-mcp-server,your-new-server
   ```

2. **Create or update** the crew's `config/tools.yaml` file to specify which agents get which tools:
   ```yaml
   # Example tools.yaml
   agent_name_tools:
     - tool_name_1
     - tool_name_2
   
   shared_tools:
     - shared_tool_name
   ```

3. **Update the crew.py** to follow the established pattern:
   ```python
   from crewai_tools import MCPServerAdapter
   
   # MCP Server configuration
   _MCP_SERVER_CONFIG = [
       {
           "url": "http://mcp-gateway:8811/mcp/",
           "transport": "streamable-http",
           "headers": {"Accept": "application/json, text/event-stream"}
       }
   ]
   
   class YourCrew:
       def _get_mcp_tools(self):
           self._mcp_adapter = MCPServerAdapter(_MCP_SERVER_CONFIG)
           self._mcp_tools = self._mcp_adapter.__enter__()
           
       def _get_tools_for_agent(self, section: str):
           # Load tools from tools.yaml and filter available MCP tools
   ```

4. **Tools are automatically discovered** - no need to modify adapter code or hard-code tool definitions

### Implementation Requirements
- **All crews using MCP tools** must use the Docker MCP Gateway pattern for consistency
- **No standalone MCP server implementations** should be created outside the gateway
- **Tool discovery is dynamic** - tools are loaded at runtime from the gateway
- **Configuration drives tool assignment** - use YAML files, not hard-coded tool lists
