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

from python_service.app.services.mcp_adapter import MCPServerAdapter


def test_follow_307_redirect_to_sse_and_fetch_tools():
    """Adapter should follow 307 redirect to SSE and retrieve tool metadata."""

    async def handler(request: Request) -> Response:
        if request.method == "POST" and request.url.path == "/servers/test/connect":
            return Response(307, headers={"location": "/sse?sessionid=abc123"})
        if request.method == "GET" and request.url.path == "/sse":
            assert request.headers.get("accept") == "text/event-stream"
            return Response(200, headers={"content-type": "text/event-stream"}, text="data: ok\n\n")
        if request.method == "GET" and request.url.path == "/servers/test/tools":
            return Response(200, json={"tools": [{"name": "foo", "description": "", "parameters": {}}]})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    transport = httpx.MockTransport(handler)
    adapter = MCPServerAdapter("http://mock")
    adapter._session = httpx.AsyncClient(transport=transport)

    asyncio.run(adapter._connect_to_server("test", {}))
    tools = adapter.get_available_tools()
    assert "test_foo" in tools
    assert adapter._connected_servers["test"]["session_id"] == "abc123"

    asyncio.run(adapter._session.aclose())
