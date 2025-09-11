# MCP Gateway Integration Guide

This guide explains how to use and extend the Model Context Protocol (MCP) gateway integration in the Trainium Job Center.

## Overview

The MCP Gateway provides a standardized way for CrewAI agents to interact with external tools and services through the Model Context Protocol. The system is designed to be extensible, allowing new MCP servers to be added without modifying agent code.

## Architecture

```
CrewAI Agents → MCP Gateway Tool → MCP Gateway Service → MCP Servers
                                                        ├── DuckDuckGo
                                                        ├── Future Server 1
                                                        └── Future Server 2
```

## Current Implementation

### Default MCP Server

- **DuckDuckGo Search**: Provides web search capabilities for research agents
  - Server: `@modelcontextprotocol/server-duckduckgo`
  - Methods: `search`
  - Use case: Research and fact-finding

### CrewAI Integration

Agents can use MCP services through the `mcp_gateway` tool:

```yaml
# In agent YAML configuration
tools:
  - web_search  # Uses MCP gateway for DuckDuckGo search
  - mcp_gateway # Direct access to MCP gateway
```

## Adding New MCP Servers

### Step 1: Configure the Server

Add the new server configuration to `docker/mcp-gateway/config/servers.yaml`:

```yaml
servers:
  # Existing DuckDuckGo server
  duckduckgo:
    description: "DuckDuckGo search MCP server"
    command: "npx"
    args:
      - "-y"
      - "@modelcontextprotocol/server-duckduckgo@latest"
    env: {}
    auto_start: true

  # Example: Add filesystem operations
  filesystem:
    description: "Filesystem operations MCP server"
    command: "npx"
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem@latest"
    env:
      ALLOWED_DIRECTORIES: "/tmp,/app/data"
    auto_start: false

  # Example: Add Brave Search
  brave_search:
    description: "Brave Search API MCP server"
    command: "npx"
    args:
      - "-y"
      - "@modelcontextprotocol/server-brave-search@latest"
    env:
      BRAVE_API_KEY: "${BRAVE_API_KEY}"
    auto_start: false
```

### Step 2: Update Gateway Configuration

Update `docker/mcp-gateway/main.py` to include the new server in `MCP_SERVERS_CONFIG`:

```python
MCP_SERVERS_CONFIG = {
    "duckduckgo": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-duckduckgo@latest"],
        "env": {},
        "description": "DuckDuckGo search MCP server"
    },
    "filesystem": {
        "command": "npx", 
        "args": ["-y", "@modelcontextprotocol/server-filesystem@latest"],
        "env": {
            "ALLOWED_DIRECTORIES": "/tmp,/app/data"
        },
        "description": "Filesystem operations MCP server"
    },
    "brave_search": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search@latest"], 
        "env": {
            "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")
        },
        "description": "Brave Search API MCP server"
    }
}
```

### Step 3: Add Environment Variables (if needed)

For servers requiring API keys or configuration, add them to your `.env` file:

```bash
# .env
BRAVE_API_KEY=your_brave_api_key_here
GITHUB_TOKEN=your_github_token_here
```

And update `docker-compose.yml` to pass the environment variables:

```yaml
services:
  mcp-gateway:
    # ... existing configuration
    environment:
      PORT: 8811
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      BRAVE_API_KEY: ${BRAVE_API_KEY}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
```

### Step 4: Update Agent Tools (Optional)

Agents can use new MCP servers in several ways:

1. **Direct server specification**:
```python
# In agent code or custom tool
result = mcp_tool._execute(
    query="search term",
    server="brave_search",  # Specify the server
    max_results=5
)
```

2. **Create server-specific tools**:
```python
# Create a Brave search specific tool
def create_brave_search_tool():
    return MCPGatewayTool(
        gateway_url="http://mcp-gateway:8811",
        default_server="brave_search"
    )
```

3. **Add to existing agent configurations**:
```yaml
# agent.yaml
tools:
  - web_search      # DuckDuckGo via MCP
  - brave_search    # Brave Search via MCP (if tool created)
  - filesystem      # Filesystem ops via MCP (if tool created)
```

## Available MCP Servers

### Official MCP Servers

Visit the [MCP Server Registry](https://github.com/modelcontextprotocol/servers) for a full list of available servers:

- **@modelcontextprotocol/server-duckduckgo**: Web search
- **@modelcontextprotocol/server-filesystem**: File operations
- **@modelcontextprotocol/server-brave-search**: Brave Search API
- **@modelcontextprotocol/server-github**: GitHub API access
- **@modelcontextprotocol/server-postgres**: PostgreSQL database access
- **@modelcontextprotocol/server-puppeteer**: Web scraping
- **@modelcontextprotocol/server-sqlite**: SQLite database access

### Custom MCP Servers

You can also create custom MCP servers for your specific needs. Follow the [MCP Server Development Guide](https://modelcontextprotocol.io/docs/building-servers) to build custom servers.

## Usage Examples

### Research Agent with Multiple Search Sources

```yaml
# researcher.yaml
tools:
  - web_search      # DuckDuckGo search
  - brave_search    # Brave search for different results
```

### Data Analysis Agent with Database Access

```yaml
# analyst.yaml  
tools:
  - postgres_query  # Database queries
  - filesystem      # File operations
```

### Web Research Agent with Scraping

```yaml
# web_researcher.yaml
tools:
  - web_search      # Initial search
  - puppeteer       # Deep web scraping
```

## Testing New MCP Servers

### 1. Test Server Availability

```bash
# Check available servers
curl http://localhost:8811/servers

# Start a specific server
curl -X POST http://localhost:8811/servers/filesystem/start

# Check server status
curl http://localhost:8811/health
```

### 2. Test Direct MCP Calls

```bash
# Test search functionality
curl -X POST http://localhost:8811/call \
  -H "Content-Type: application/json" \
  -d '{
    "server": "duckduckgo",
    "method": "search", 
    "params": {
      "query": "Python programming",
      "max_results": 3
    }
  }'
```

### 3. Test in CrewAI Agent

```python
# Quick test script
from app.services.crewai.tools.mcp_gateway import create_mcp_gateway_tool

tool = create_mcp_gateway_tool()
result = tool._execute("Python programming", server="duckduckgo")
print(result)
```

## Troubleshooting

### Common Issues

1. **Server won't start**: Check if the NPM package exists and environment variables are set
2. **Connection refused**: Ensure MCP gateway service is running and accessible
3. **API key errors**: Verify environment variables are properly passed to containers

### Debug Commands

```bash
# Check MCP gateway logs
docker-compose logs mcp-gateway

# Check if gateway is responding
curl http://localhost:8811/health

# List available servers
curl http://localhost:8811/servers

# Test direct server communication
curl -X POST http://localhost:8811/call -H "Content-Type: application/json" -d '{"server":"duckduckgo","method":"search","params":{"query":"test"}}'
```

## Best Practices

1. **Server Selection**: Choose the right MCP server for your agent's needs
2. **Error Handling**: Always implement fallback mechanisms for MCP calls
3. **Rate Limiting**: Be mindful of API rate limits for external services
4. **Security**: Use environment variables for API keys and sensitive configuration
5. **Monitoring**: Monitor MCP server health and performance
6. **Documentation**: Document custom server configurations and usage patterns

## Future Enhancements

- **Auto-discovery**: Automatically discover available MCP servers
- **Load balancing**: Distribute requests across multiple server instances
- **Caching**: Cache MCP server responses for improved performance
- **Monitoring**: Add detailed metrics and monitoring for MCP operations
- **Custom routing**: Route requests to optimal servers based on query type