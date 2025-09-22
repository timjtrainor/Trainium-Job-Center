import asyncio
import pytest
import httpx
from httpx import Response, Request
import sys
import types

# Provide stub mcp module so tests can run without actual dependency
mcp_module = types.ModuleType("mcp")
mcp_module.ClientSession = object
mcp_types = types.ModuleType("mcp.types")
class Tool(dict):
    pass
mcp_types.Tool = Tool
mcp_module.types = mcp_types
sys.modules["mcp"] = mcp_module
sys.modules["mcp.types"] = mcp_types

from python_service.app.services.mcp_adapter import MCPServerAdapter, AdapterConfig


class TestProperMCPGatewayConnection:
    """Test suite for proper Docker MCP Gateway connection implementation."""

    def test_follow_307_redirect_to_sse_and_extract_sessionid(self):
        """Test proper 307 redirect handling for SSE endpoint discovery."""

        async def handler(request: Request) -> Response:
            if request.method == "GET" and request.url.path == "/health":
                return Response(200, json={"status": "healthy"})
            if request.method == "GET" and request.url.path == "/servers":
                return Response(307, headers={"location": "/sse?sessionid=abc123"})
            if request.method == "GET" and request.url.path == "/sse":
                assert request.headers.get("accept") == "text/event-stream"
                return Response(200, headers={"content-type": "text/event-stream"}, text="data: ok\n\n")
            if request.method == "GET" and request.url.path == "/servers/duckduckgo/tools":
                return Response(200, json={"tools": [{"name": "web_search", "description": "Search the web", "parameters": {}}]})
            if request.method == "GET" and request.url.path == "/servers/linkedin-mcp-server/tools":
                return Response(200, json={"tools": [{"name": "search_jobs", "description": "Search LinkedIn jobs", "parameters": {}}]})
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        transport = httpx.MockTransport(handler)
        config = AdapterConfig(gateway_url="http://mock")
        adapter = MCPServerAdapter(config)
        adapter._session = httpx.AsyncClient(transport=transport, follow_redirects=False)

        asyncio.run(adapter.connect())
        
        # Verify proper redirect handling
        assert adapter._sse_endpoint == "http://mock/sse?sessionid=abc123"
        assert adapter._session_id == "abc123"
        
        # Verify server discovery
        servers = adapter.list_servers()
        assert "duckduckgo" in servers
        assert "linkedin-mcp-server" in servers
        
        # Verify tool discovery
        tools = adapter.get_all_tools()
        assert "duckduckgo_web_search" in tools
        assert "linkedin-mcp-server_search_jobs" in tools
        
        # Verify tool metadata
        duckduckgo_tool = tools["duckduckgo_web_search"]
        assert duckduckgo_tool["server"] == "duckduckgo"
        assert duckduckgo_tool["original_name"] == "web_search"

        asyncio.run(adapter._session.aclose())

    def test_200_response_with_server_list(self):
        """Test handling 200 response with direct server list."""

        async def handler(request: Request) -> Response:
            if request.method == "GET" and request.url.path == "/health":
                return Response(200, json={"status": "healthy"})
            if request.method == "GET" and request.url.path == "/servers":
                return Response(200, json={
                    "server1": {"endpoint": "http://server1"},
                    "server2": {"endpoint": "http://server2"}
                })
            if request.url.path.endswith("/tools"):
                return Response(200, json={"tools": []})
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        transport = httpx.MockTransport(handler)
        config = AdapterConfig(gateway_url="http://mock")
        adapter = MCPServerAdapter(config)
        adapter._session = httpx.AsyncClient(transport=transport, follow_redirects=False)

        asyncio.run(adapter.connect())
        
        # Verify direct server list handling
        servers = adapter.list_servers()
        assert "server1" in servers
        assert "server2" in servers
        assert adapter._sse_endpoint is None

        asyncio.run(adapter._session.aclose())

    def test_configurable_timeouts(self):
        """Test configurable timeout settings."""
        
        config = AdapterConfig(
            gateway_url="http://test",
            connection_timeout=10,
            discovery_timeout=20,
            execution_timeout=30
        )
        
        adapter = MCPServerAdapter(config)
        
        assert adapter.config.connection_timeout == 10
        assert adapter.config.discovery_timeout == 20
        assert adapter.config.execution_timeout == 30

    def test_tool_execution_through_shared_transport(self):
        """Test tool execution using shared transport."""

        async def handler(request: Request) -> Response:
            if request.method == "GET" and request.url.path == "/health":
                return Response(200, json={"status": "healthy"})
            if request.method == "GET" and request.url.path == "/servers":
                return Response(307, headers={"location": "/sse?sessionid=test123"})
            if request.method == "GET" and request.url.path == "/sse":
                return Response(200, headers={"content-type": "text/event-stream"})
            if request.method == "GET" and request.url.path == "/servers/duckduckgo/tools":
                return Response(200, json={"tools": [{"name": "web_search", "description": "Search", "parameters": {}}]})
            if request.method == "POST" and request.url.path == "/servers/duckduckgo/tools/web_search/execute":
                # Verify request format
                body = request.read()
                data = httpx._content.json_loads(body)
                assert data["session_id"] == "test123"
                assert "arguments" in data
                return Response(200, json={"result": "Search completed"})
            if request.url.path.endswith("/tools"):
                return Response(200, json={"tools": []})
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        transport = httpx.MockTransport(handler)
        config = AdapterConfig(gateway_url="http://mock")
        adapter = MCPServerAdapter(config)
        adapter._session = httpx.AsyncClient(transport=transport, follow_redirects=False)

        asyncio.run(adapter.connect())
        
        # Test tool execution
        result = asyncio.run(adapter.execute_tool("duckduckgo", "web_search", {"query": "test"}))
        assert result["result"] == "Search completed"

        asyncio.run(adapter._session.aclose())

    def test_error_handling_missing_location_header(self):
        """Test error handling for missing Location header in 307 response."""

        async def handler(request: Request) -> Response:
            if request.method == "GET" and request.url.path == "/health":
                return Response(200, json={"status": "healthy"})
            if request.method == "GET" and request.url.path == "/servers":
                return Response(307)  # Missing Location header
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        transport = httpx.MockTransport(handler)
        config = AdapterConfig(gateway_url="http://mock")
        adapter = MCPServerAdapter(config)
        adapter._session = httpx.AsyncClient(transport=transport, follow_redirects=False)

        # Should raise error for malformed redirect
        with pytest.raises(ValueError, match="307 redirect missing Location header"):
            asyncio.run(adapter.connect())

        asyncio.run(adapter._session.aclose())

    def test_health_check_failure(self):
        """Test handling of gateway health check failure."""

        async def handler(request: Request) -> Response:
            if request.method == "GET" and request.url.path == "/health":
                return Response(503, json={"status": "unhealthy"})
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        transport = httpx.MockTransport(handler)
        config = AdapterConfig(gateway_url="http://mock")
        adapter = MCPServerAdapter(config)
        adapter._session = httpx.AsyncClient(transport=transport, follow_redirects=False)

        # Should raise connection error for failed health check
        with pytest.raises(ConnectionError, match="Gateway health check failed"):
            asyncio.run(adapter.connect())

        asyncio.run(adapter._session.aclose())

    def test_server_filtering_by_name(self):
        """Test tool filtering by server name."""

        async def handler(request: Request) -> Response:
            if request.method == "GET" and request.url.path == "/health":
                return Response(200, json={"status": "healthy"})
            if request.method == "GET" and request.url.path == "/servers":
                return Response(307, headers={"location": "/sse"})
            if request.method == "GET" and request.url.path == "/sse":
                return Response(200, headers={"content-type": "text/event-stream"})
            if request.method == "GET" and request.url.path == "/servers/duckduckgo/tools":
                return Response(200, json={"tools": [{"name": "search", "description": "Search", "parameters": {}}]})
            if request.method == "GET" and request.url.path == "/servers/linkedin-mcp-server/tools":
                return Response(200, json={"tools": [{"name": "jobs", "description": "Jobs", "parameters": {}}]})
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")

        transport = httpx.MockTransport(handler)
        config = AdapterConfig(gateway_url="http://mock")
        adapter = MCPServerAdapter(config)
        adapter._session = httpx.AsyncClient(transport=transport, follow_redirects=False)

        asyncio.run(adapter.connect())
        
        # Test server-specific tool listing
        duckduckgo_tools = adapter.list_tools("duckduckgo")
        linkedin_tools = adapter.list_tools("linkedin-mcp-server")
        
        assert len(duckduckgo_tools) == 1
        assert "duckduckgo_search" in duckduckgo_tools
        
        assert len(linkedin_tools) == 1
        assert "linkedin-mcp-server_jobs" in linkedin_tools

        asyncio.run(adapter._session.aclose())

    def test_diagnostics_information(self):
        """Test diagnostic information for troubleshooting."""
        
        config = AdapterConfig(gateway_url="http://test", connection_timeout=15)
        adapter = MCPServerAdapter(config)
        
        diagnostics = adapter.get_diagnostics()
        
        assert diagnostics["connected"] == False
        assert diagnostics["gateway_url"] == "http://test"
        assert diagnostics["config"]["connection_timeout"] == 15
        assert isinstance(diagnostics["servers"], list)
        assert isinstance(diagnostics["tools"], list)
