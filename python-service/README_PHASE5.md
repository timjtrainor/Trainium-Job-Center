# Phase 5: CrewAI Integration and Examples

This document describes the Phase 5 implementation of the MCP Gateway integration, which provides CrewAI-compatible wrappers and comprehensive usage examples.

## Overview

Phase 5 builds upon the complete MCP adapter system from Phases 1-4 to provide seamless integration with CrewAI agents and other AI frameworks. The implementation includes both async-native and sync wrappers, comprehensive examples, and full test coverage.

## Key Components

### 1. AsyncMCPToolWrapper (Preferred)

The `AsyncMCPToolWrapper` provides async-native access to MCP tools, making it ideal for frameworks that support async operations.

```python
from app.services.mcp import MCPGatewayAdapter, StreamingTransport, AsyncMCPToolWrapper

# Create adapter and tool wrapper
transport = StreamingTransport("http://localhost:8811")
adapter = MCPGatewayAdapter(transport=transport)

async with adapter:
    wrapper = AsyncMCPToolWrapper(adapter, "web_search")
    await wrapper.initialize()
    
    result = await wrapper.execute(query="Python async programming")
    print(result)
```

### 2. MCPToolWrapper (CrewAI Compatible)

The `MCPToolWrapper` extends CrewAI's `BaseTool` class for seamless integration with CrewAI agents.

```python
from crewai import Agent, Task, Crew
from app.services.mcp import MCPToolFactory

# Create CrewAI-compatible tools
async with adapter:
    factory = MCPToolFactory(adapter)
    mcp_tools = await factory.create_crewai_tools()
    
    # Use with CrewAI agents
    researcher = Agent(
        role='Research Specialist',
        goal='Conduct research using MCP tools',
        backstory='Expert researcher with access to MCP gateway tools',
        tools=list(mcp_tools.values())
    )
```

### 3. MCPToolFactory

The `MCPToolFactory` provides convenient methods for creating tool wrappers in bulk or individually.

```python
from app.services.mcp import MCPToolFactory

factory = MCPToolFactory(adapter)

# Create all available tools
async_tools = await factory.create_async_tools()
crewai_tools = await factory.create_crewai_tools()

# Create single tools
search_tool = await factory.create_single_async_tool("web_search")
calc_tool = factory.create_single_crewai_tool("calculator")
```

## Installation

### Basic Installation

The async functionality is available with the base MCP implementation:

```bash
# Core MCP functionality (always available)
pip install fastapi uvicorn httpx loguru
```

### Full CrewAI Integration

For full CrewAI integration, install the additional dependencies:

```bash
# CrewAI integration
pip install crewai crewai-tools

# Enhanced schema support
pip install pydantic
```

### Check Integration Status

```python
from app.services.mcp import get_integration_status

status = get_integration_status()
print(status)
# {
#   "crewai_available": True,
#   "pydantic_available": True, 
#   "full_functionality": True,
#   "async_tools_available": True,
#   "sync_tools_available": True
# }
```

## Examples

Phase 5 includes four comprehensive examples:

### 1. Basic Usage (`examples/basic_usage.py`)

Demonstrates fundamental MCP Gateway usage patterns:
- Manual and environment-based configuration
- Tool discovery and execution
- Basic error handling
- Connection lifecycle management

```bash
python examples/basic_usage.py
```

### 2. CrewAI Integration (`examples/crewai_integration.py`)

Shows how to integrate MCP tools with CrewAI agents:
- Creating agents with MCP tools
- Running crews with tool access
- Async vs sync tool patterns
- Graceful fallback when gateway unavailable

```bash
python examples/crewai_integration.py
```

### 3. Error Handling (`examples/error_handling.py`)

Comprehensive error handling patterns:
- Connection failures and retries
- Tool execution errors  
- Resource cleanup patterns
- Graceful degradation strategies

```bash
python examples/error_handling.py
```

### 4. Health Monitoring (`examples/health_monitoring.py`)

Health monitoring and metrics collection:
- Connection health checks
- Performance metrics
- Continuous monitoring with alerts
- Dashboard-style reporting

```bash
python examples/health_monitoring.py
```

## Configuration

### Environment Variables

```bash
# MCP Gateway connection
MCP_GATEWAY_URL=http://localhost:8811
MCP_TRANSPORT_TYPE=streaming
MCP_TIMEOUT=30
MCP_MAX_RETRIES=3

# Logging
MCP_LOG_LEVEL=INFO
```

### Programmatic Configuration

```python
from app.services.mcp import MCPConfig, StreamingTransport, MCPGatewayAdapter

# Method 1: Environment-based
adapter = MCPConfig.from_environment()

# Method 2: Manual configuration
transport = StreamingTransport("http://localhost:8811")
adapter = MCPGatewayAdapter(
    transport=transport,
    timeout=30,
    max_retries=3,
    log_level="INFO"
)
```

## Architecture

### Async-First Design

Phase 5 prioritizes async operations for better performance:

```python
# Preferred: Async-native tools
async_tools = await factory.create_async_tools()
result = await async_tools["web_search"].execute(query="test")

# Fallback: Sync tools for CrewAI compatibility
crewai_tools = await factory.create_crewai_tools() 
result = crewai_tools["web_search"]._run(query="test")
```

### Graceful Degradation

The implementation gracefully handles missing dependencies:

```python
# Works even without CrewAI installed
from app.services.mcp import is_crewai_available

if is_crewai_available():
    # Full CrewAI integration
    crewai_tools = await factory.create_crewai_tools()
else:
    # Async-only functionality
    async_tools = await factory.create_async_tools()
```

### Schema Conversion

MCP tool schemas are automatically converted to Pydantic models:

```python
# MCP schema
{
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search query"},
        "limit": {"type": "integer", "description": "Result limit"}
    },
    "required": ["query"]
}

# Becomes Pydantic model for CrewAI
class WebSearchArgs(BaseModel):
    query: str = Field(description="Search query")
    limit: Optional[int] = Field(default=None, description="Result limit")
```

## Testing 

Phase 5 includes comprehensive tests covering all components:

```bash
# Run all Phase 5 tests
pytest tests/mcp/test_crewai_integration.py -v

# Test specific components
pytest tests/mcp/test_crewai_integration.py::TestAsyncMCPToolWrapper -v
pytest tests/mcp/test_crewai_integration.py::TestMCPToolWrapper -v  
pytest tests/mcp/test_crewai_integration.py::TestMCPToolFactory -v
```

### Test Coverage

- AsyncMCPToolWrapper functionality
- MCPToolWrapper CrewAI compatibility
- MCPToolFactory bulk operations
- Schema conversion (MCP to Pydantic)
- Error handling and propagation
- Integration scenarios and workflows

## Monitoring and Observability

Phase 5 integrates with existing monitoring infrastructure:

### Health Checks

```python
from app.services.mcp import MCPHealthMonitor

monitor = MCPHealthMonitor(adapter)
health = await monitor.check_health()

print(f"Status: {health.is_healthy}")
print(f"Response time: {health.response_time}s")
```

### Metrics Collection

```python
# Get performance metrics
metrics = await monitor.get_metrics()

print(f"Uptime: {metrics.uptime}s")
print(f"Success rate: {metrics.success_rate:.1%}")
print(f"Avg response time: {metrics.avg_response_time:.3f}s")
```

### Integration with Monitoring Systems

```python
# Kubernetes-style health check
async def k8s_health_check():
    try:
        health = await monitor.check_health()
        return {"status": "healthy"} if health.is_healthy else {"status": "degraded"}
    except Exception:
        return {"status": "unhealthy"}

# Prometheus metrics
async def prometheus_metrics():
    metrics = await monitor.get_metrics()
    return f"""
    mcp_gateway_connected 1
    mcp_gateway_healthy {1 if health.is_healthy else 0}
    mcp_gateway_response_time {health.response_time}
    mcp_gateway_requests_total {metrics.request_count}
    """
```

## Best Practices

### 1. Prefer Async Tools

Use `AsyncMCPToolWrapper` when possible for better performance:

```python
# Good: Direct async usage
async_tools = await factory.create_async_tools()
result = await async_tools["search"].execute(query="test")

# Okay: CrewAI compatibility (adds overhead)
crewai_tools = await factory.create_crewai_tools()
result = crewai_tools["search"]._run(query="test")
```

### 2. Handle Connection Failures

Always use context managers and handle connection failures:

```python
try:
    async with adapter:
        tools = await factory.create_async_tools()
        # Use tools...
except ConnectionError:
    # Fallback to offline mode or alternative tools
    pass
```

### 3. Resource Management

Use context managers for automatic cleanup:

```python
# Automatic cleanup guaranteed
async with MCPGatewayAdapter(transport) as adapter:
    # Work with adapter...
    pass  # Cleanup happens automatically
```

### 4. Error Propagation

Handle tool execution errors appropriately:

```python
try:
    result = await tool.execute(query="test")
except ToolExecutionError as e:
    # Handle tool-specific errors
    logger.error(f"Tool execution failed: {e}")
except MCPError as e:
    # Handle broader MCP errors
    logger.error(f"MCP error: {e}")
```

## Troubleshooting

### Common Issues

1. **CrewAI Not Available**
   ```
   ModuleNotFoundError: No module named 'crewai_tools'
   ```
   **Solution**: Install CrewAI dependencies or use async tools only.

2. **Gateway Connection Failed**
   ```
   ConnectionError: Failed to connect to MCP Gateway
   ```
   **Solution**: Ensure MCP Gateway is running on the configured URL.

3. **Tool Execution Timeout**
   ```
   TimeoutError: Tool execution timed out
   ```
   **Solution**: Increase timeout or check tool implementation.

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
adapter = MCPGatewayAdapter(
    transport=transport,
    log_level="DEBUG"  # Enables detailed logging
)
```

## Performance Considerations

### Connection Pooling

The adapter manages connections efficiently:

```python
# Reuse connections when possible
async with adapter:
    # Multiple operations share the same connection
    tools1 = await factory.create_async_tools()
    tools2 = await factory.create_crewai_tools() 
    result = await tools1["search"].execute(query="test")
```

### Concurrent Operations

Tools support concurrent execution:

```python
# Execute multiple tools concurrently
tasks = [
    tools["search"].execute(query="query1"),
    tools["calculator"].execute(expression="2+2"),
    tools["search"].execute(query="query2")
]

results = await asyncio.gather(*tasks)
```

## Migration from Earlier Phases

Phase 5 is fully backward compatible with earlier phases:

```python
# Phase 4 code continues to work
from app.services.mcp import MCPGatewayAdapter, StreamingTransport

# Phase 5 adds new capabilities
from app.services.mcp import AsyncMCPToolWrapper, MCPToolFactory
```

## Future Enhancements

Potential Phase 6 improvements:
- Additional AI framework integrations (LangChain, AutoGen, etc.)
- Advanced tool orchestration patterns
- Enhanced monitoring and alerting
- Tool result caching and optimization
- Distributed tool execution

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Run the demo script: `python phase5_demo.py`
3. Review example implementations in `examples/`
4. Check test cases for usage patterns
5. Enable debug logging for detailed diagnostics