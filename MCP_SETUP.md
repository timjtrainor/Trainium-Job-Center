# MCP Gateway Setup Guide

This guide explains how to set up and troubleshoot the Docker MCP Gateway with stdio transport.

## Quick Setup

1. **Run the setup script to pull required images:**
   ```bash
   ./setup-mcp.sh
   ```

2. **Start the services:**
   ```bash
   docker-compose up -d
   ```

3. **Check gateway health:**
   ```bash
   curl http://localhost:8811/health
   ```

## Architecture

The MCP Gateway uses a hybrid approach:
- **Internal Communication**: stdio transport for connecting to MCP servers
- **External API**: HTTP REST API for adapter connections
- **Server Management**: Docker containers for individual MCP servers

## Configuration

### MCP Gateway (docker-compose.yml)
```yaml
mcp-gateway:
  image: docker/mcp-gateway
  command:
    - --servers=duckduckgo,linkedin-mcp-server
    - --transport=stdio  # Internal transport
    - --port=8811       # HTTP REST API port
    - --verbose         # Detailed logging
```

### MCP Servers (python-service/mcp-config/servers.json)
```json
{
  "servers": {
    "duckduckgo": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/duckduckgo"],
      "description": "DuckDuckGo search server"
    },
    "linkedin-mcp-server": {
      "command": "docker", 
      "args": ["run", "-i", "--rm", "-e", "LINKEDIN_COOKIE", "stickerdaniel/linkedin-mcp-server"],
      "env": {
        "LINKEDIN_COOKIE": "${LINKEDIN_COOKIE}"
      },
      "description": "LinkedIn MCP server"
    }
  }
}
```

## Troubleshooting

### Gateway Keeps Restarting

**Most Common Cause**: Missing MCP server Docker images

**Solution**:
1. Pull required images:
   ```bash
   docker pull mcp/duckduckgo
   docker pull stickerdaniel/linkedin-mcp-server
   ```

2. Or run the setup script:
   ```bash
   ./setup-mcp.sh
   ```

### Check Gateway Logs

```bash
# View real-time logs
docker logs -f trainium_mcp_gateway

# View recent logs
docker logs trainium_mcp_gateway --tail 100
```

### Verify Configuration

Run the diagnostic script:
```bash
cd python-service
python debug_mcp_gateway.py
```

### Test Individual Components

1. **Test MCP Gateway image:**
   ```bash
   docker run --rm docker/mcp-gateway --help
   ```

2. **Test DuckDuckGo server:**
   ```bash
   docker run --rm -i mcp/duckduckgo --help
   ```

3. **Test adapter connectivity:**
   ```bash
   cd python-service
   python test_stdio_gateway_adapter.py
   ```

## Common Issues

### 1. Docker Socket Permission Issues
```bash
# Check socket permissions
ls -la /var/run/docker.sock

# If needed, add user to docker group
sudo usermod -aG docker $USER
```

### 2. Port Conflicts
```bash
# Check if port 8811 is in use
netstat -tuln | grep 8811
```

### 3. Image Pull Failures
```bash
# Check Docker Hub connectivity
docker pull hello-world

# Try pulling images manually
docker pull mcp/duckduckgo
docker pull stickerdaniel/linkedin-mcp-server
```

### 4. Environment Variables
For LinkedIn MCP server, ensure `LINKEDIN_COOKIE` is set:
```bash
export LINKEDIN_COOKIE="your_linkedin_cookie_here"
```

## Gateway Startup Process

1. **Initialization**: Gateway starts with stdio transport
2. **Server Discovery**: Reads `/config/servers.json` 
3. **Image Pulling**: Downloads required Docker images (if not present)
4. **Server Launch**: Starts MCP server containers
5. **API Ready**: HTTP REST API becomes available on port 8811

## Success Indicators

- Gateway health check returns 200: `curl http://localhost:8811/health`
- Gateway logs show "stdio started successfully"
- Server endpoints are accessible: `curl http://localhost:8811/servers`
- No restart loops in docker logs

## Integration with Python Service

The Python service MCP adapter connects to the gateway via HTTP REST API:

```python
from app.services.mcp_adapter import MCPServerAdapter, AdapterConfig

config = AdapterConfig(gateway_url="http://mcp-gateway:8811")
async with MCPServerAdapter(config) as adapter:
    servers = adapter.list_servers()
    tools = adapter.get_all_tools()
```

The adapter handles:
- Gateway health checks
- Server discovery and connection
- Tool discovery and execution
- Session management
- Error handling and retries