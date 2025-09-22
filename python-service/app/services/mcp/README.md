# MCP (Model Context Protocol) Integration - Phase 4

This directory contains the complete MCP (Model Context Protocol) integration for the Trainium Job Center, including the Phase 4 main adapter class that ties everything together.

## Overview

The MCP integration provides a unified interface for communicating with MCP gateways and executing tools through the Model Context Protocol. Phase 4 introduces the main adapter class that coordinates all components and provides a high-level interface for MCP operations.

## Architecture

```
MCP Integration (Phase 4)
├── Transport Layer (Phase 1)
│   ├── MCPTransport (abstract base)
│   ├── StdioTransport (stdin/stdout communication)
│   └── StreamingTransport (HTTP streaming)
├── Protocol Layer (Phase 2)
│   ├── MCPProtocol (handshake & message exchange)
│   ├── MCPSession (session lifecycle management)
│   └── JSON-RPC models and validation
├── Tool Layer (Phase 3)
│   ├── MCPToolManager (tool discovery & execution)
│   ├── ToolDiscoveryService (multi-manager coordination)
│   └── ResultNormalizer (result standardization)
└── Main Adapter Layer (Phase 4) ⭐
    ├── MCPGatewayAdapter (main coordination class)
    ├── MCPConfig (configuration management)
    └── MCPHealthMonitor (health monitoring & metrics)
```

## Phase 4 Components

### MCPGatewayAdapter

The main adapter class that coordinates between transport, protocol, and tools components.

**Key Features:**
- Connection management with retry logic and exponential backoff
- Context manager support for automatic resource management
- Tool discovery and execution coordination
- Comprehensive error handling and logging
- Metrics collection and performance tracking

**Usage:**
```python
from app.services.mcp import MCPGatewayAdapter, StdioTransport

# Create adapter
transport = StdioTransport()
adapter = MCPGatewayAdapter(
    transport=transport,
    timeout=30,
    max_retries=3,
    log_level="INFO"
)

# Use as context manager
async with adapter as gateway:
    tools = await gateway.list_tools()
    result = await gateway.execute_tool("my_tool", {"arg": "value"})
    health = await gateway.health_check()
```

### MCPConfig

Configuration management with environment variable support and validation.

**Key Features:**
- Environment variable configuration loading
- Dictionary-based configuration with defaults
- Comprehensive validation with clear error messages
- Support for both stdio and streaming transports
- Test configuration utilities

**Usage:**
```python
from app.services.mcp import MCPConfig

# From environment variables
adapter = MCPConfig.from_environment()

# From dictionary
config = {
    "transport_type": "stdio",
    "timeout": 30,
    "max_retries": 3,
    "log_level": "INFO"
}
adapter = MCPConfig.from_dict(config)

# Get configuration info
info = MCPConfig.get_config_info()
```

**Environment Variables:**
- `MCP_GATEWAY_URL`: Gateway URL for streaming transport (default: `http://mcp-gateway:8811`)
- `MCP_GATEWAY_TRANSPORT`: Transport type - `streaming` or `stdio` (default: `streaming`)
- `MCP_GATEWAY_TIMEOUT`: Operation timeout in seconds (default: `30`)
- `MCP_GATEWAY_MAX_RETRIES`: Maximum retry attempts (default: `3`)
- `MCP_LOG_LEVEL`: Logging level (default: `INFO`)

### MCPHealthMonitor

Health monitoring and metrics collection for MCP operations.

**Key Features:**
- Comprehensive health checks with status reporting
- Automatic monitoring with configurable intervals
- Performance threshold monitoring (error rate, response time)
- Metric history and snapshots
- Health check registry for multiple monitors

**Usage:**
```python
from app.services.mcp import MCPHealthMonitor

# Create health monitor
monitor = MCPHealthMonitor(adapter, check_interval=60)

# Perform health check
result = await monitor.health_check()
print(f"Status: {result.status}")
print(f"Errors: {result.errors}")

# Start automatic monitoring
await monitor.start_monitoring()

# Get metrics
metrics = monitor.get_metrics()
summary = monitor.get_health_summary()
```

## Quick Start

### 1. Basic Usage

```python
import asyncio
from app.services.mcp import MCPConfig

async def main():
    # Create adapter from environment
    adapter = MCPConfig.from_environment()
    
    # Use adapter
    async with adapter as gateway:
        # Discover available tools
        tools = await gateway.list_tools()
        print(f"Available tools: {list(tools.keys())}")
        
        # Execute a tool
        if tools:
            tool_name = list(tools.keys())[0]
            result = await gateway.execute_tool(tool_name, {})
            print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Configuration Management

```python
from app.services.mcp import MCPConfig, ConfigurationError

# Custom configuration
config = {
    "transport_type": "stdio",
    "timeout": 15,
    "max_retries": 2,
    "log_level": "DEBUG"
}

try:
    adapter = MCPConfig.from_dict(config)
    print("Configuration valid!")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

### 3. Health Monitoring

```python
from app.services.mcp import MCPConfig, MCPHealthMonitor

async def monitor_health():
    adapter = MCPConfig.from_environment()
    monitor = MCPHealthMonitor(adapter, check_interval=30)
    
    # Single health check
    health = await monitor.health_check()
    print(f"System status: {health.status}")
    
    # Continuous monitoring
    await monitor.start_monitoring()
    
    # Let it run for a while
    await asyncio.sleep(120)
    
    # Stop monitoring
    await monitor.stop_monitoring()
    
    # Get metrics
    metrics = monitor.get_metrics()
    print(f"Health checks performed: {len(monitor.get_metric_history())}")
```

## Error Handling

The Phase 4 implementation includes comprehensive error handling:

### Configuration Errors
```python
from app.services.mcp import ConfigurationError

try:
    MCPConfig.from_dict({"transport_type": "invalid"})
except ConfigurationError as e:
    print(f"Invalid configuration: {e}")
```

### Connection Errors
```python
from app.services.mcp import MCPError

adapter = MCPConfig.from_environment()

try:
    async with adapter as gateway:
        tools = await gateway.list_tools()
except MCPError as e:
    print(f"MCP operation failed: {e}")
```

## Testing

### Running Tests

The implementation includes comprehensive test coverage:

```bash
# Python compilation check
python -m py_compile $(git ls-files '*.py' | grep mcp)

# Simple validation test (no external dependencies)
python test_phase4_simple.py

# Comprehensive test suite (requires pytest)
python -m pytest tests/test_mcp_adapter.py -v
```

### Demo Script

```bash
# Run the Phase 4 demonstration
python phase4_demo.py
```

## Integration with Existing Systems

### CrewAI Integration (Next Phase)

Phase 4 provides the foundation for CrewAI integration:

```python
# Future CrewAI integration pattern
from crewai import Agent, Task, Crew
from app.services.mcp import MCPConfig

async def crewai_with_mcp():
    # Create MCP adapter
    adapter = MCPConfig.from_environment()
    
    async with adapter as gateway:
        # Discover MCP tools
        tools = await gateway.list_tools()
        
        # Create CrewAI agents with MCP tools
        agent = Agent(
            role="MCP Tool User",
            goal="Execute tasks using MCP tools",
            tools=list(tools.keys())  # MCP tools available to agent
        )
        
        # Execute crew with MCP integration
        crew = Crew(agents=[agent], tasks=[...])
        result = crew.kickoff()
```

### FastAPI Endpoints

Integration with the existing FastAPI service:

```python
from fastapi import APIRouter, HTTPException
from app.services.mcp import MCPConfig

router = APIRouter(prefix="/mcp", tags=["MCP Gateway"])

@router.get("/health")
async def mcp_health():
    adapter = MCPConfig.from_environment()
    monitor = MCPHealthMonitor(adapter)
    
    try:
        health = await monitor.health_check()
        return {
            "status": health.status,
            "details": health.details,
            "errors": health.errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools")
async def list_mcp_tools():
    adapter = MCPConfig.from_environment()
    
    try:
        async with adapter as gateway:
            tools = await gateway.list_tools()
            return {"tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Files Structure

```
app/services/mcp/
├── __init__.py                  # Package exports and imports
├── README.md                    # This documentation
├── mcp_transport.py            # Phase 1: Transport layer implementations
├── mcp_models.py               # Phase 1: JSON-RPC message models
├── mcp_exceptions.py           # Phase 1: Exception hierarchy
├── mcp_logging.py              # Phase 1: Structured logging
├── mcp_protocol.py             # Phase 2: Protocol handling
├── mcp_session.py              # Phase 2: Session management
├── mcp_tools.py                # Phase 3: Tool discovery & execution
├── mcp_results.py              # Phase 3: Result normalization
├── mcp_adapter.py              # Phase 4: Main adapter class ⭐
├── mcp_config.py               # Phase 4: Configuration management ⭐
└── mcp_health.py               # Phase 4: Health monitoring ⭐
```

## Dependencies

The implementation uses minimal dependencies:

**Core Dependencies:**
- `asyncio` - Async I/O operations
- `json` - JSON serialization  
- `logging` - Structured logging
- `dataclasses` - Message model structures
- `jsonschema` - JSON schema validation

**Optional Dependencies:**
- `structlog` - Enhanced structured logging
- `aiohttp` - Full HTTP streaming transport implementation

## Security Considerations

1. **Transport Security**: Use HTTPS for streaming transport in production
2. **Authentication**: Implement authentication for MCP gateway connections
3. **Validation**: All tool arguments are validated against schemas
4. **Error Handling**: Sensitive information is not exposed in error messages
5. **Logging**: Structured logging with appropriate log levels

## Performance Considerations

### Connection Pooling

For high-throughput scenarios, consider implementing connection pooling:

```python
from app.services.mcp import MCPSessionPool

# Use session pool for multiple concurrent connections
pool = MCPSessionPool(max_sessions=10)

async def execute_with_pool(tool_name, arguments):
    session = await pool.get_session("default", transport, timeout=30)
    # Use session for tool execution
```

### Health Monitoring

Configure appropriate monitoring intervals based on usage:

```python
# High-frequency monitoring for critical systems
monitor = MCPHealthMonitor(adapter, check_interval=10)

# Lower frequency for development environments
monitor = MCPHealthMonitor(adapter, check_interval=300)
```

## Troubleshooting

### Common Issues

1. **Configuration Errors**
   - Check environment variables are set correctly
   - Validate transport type and other configuration values
   - Use `MCPConfig.get_config_info()` to see current configuration

2. **Connection Issues**  
   - Verify MCP gateway is running and accessible
   - Check network connectivity and firewall settings
   - Review connection logs for detailed error information

3. **Tool Execution Failures**
   - Validate tool arguments against schema
   - Check tool availability with `list_tools()`
   - Review tool execution logs for specific errors

4. **Health Check Issues**
   - Adjust health check thresholds for your environment
   - Monitor health check frequency and performance impact
   - Use health summaries to identify recurring issues

### Debug Logging

Enable debug logging for detailed troubleshooting:

```python
adapter = MCPGatewayAdapter(
    transport=transport,
    log_level="DEBUG"  # Enable debug logging
)
```

## Migration Guide

### From Previous Phases

If you're migrating from direct usage of previous phase components:

```python
# Old way (Phase 1-3 direct usage)
transport = StdioTransport()
protocol = MCPProtocol(transport, timeout=30)
tool_manager = MCPToolManager(protocol)

await transport.connect()
await protocol.initialize()
tools = await tool_manager.discover_tools()

# New way (Phase 4 adapter)
adapter = MCPConfig.from_environment()
async with adapter as gateway:
    tools = await gateway.list_tools()
```

## Contributing

When adding new features to the MCP integration:

1. Follow the existing patterns and architecture
2. Add comprehensive error handling
3. Include structured logging
4. Write tests for new functionality
5. Update documentation

## Future Enhancements

Planned improvements for future phases:

- **Connection Pooling**: Support for multiple concurrent connections
- **Caching**: Tool discovery and schema caching
- **Metrics Export**: Prometheus/OpenTelemetry integration
- **Advanced Health Checks**: Custom health check plugins
- **Configuration Hot Reload**: Dynamic configuration updates
- **Tool Composition**: Chaining and composition of MCP tools