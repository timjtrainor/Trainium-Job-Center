import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
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

PYTHON_SERVICE_PATH = Path(__file__).resolve().parents[2] / "python-service"
if str(PYTHON_SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(PYTHON_SERVICE_PATH))

if "python_service" not in sys.modules:
    python_service_pkg = types.ModuleType("python_service")
    python_service_pkg.__path__ = [str(PYTHON_SERVICE_PATH)]
    sys.modules["python_service"] = python_service_pkg

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


def test_get_duckduckgo_tools_loads_all_prefix_tools(monkeypatch):
    """DuckDuckGo helper should return every prefixed tool exposed by the gateway."""

    from python_service.app.services.crewai import base

    available_tools = {
        "duckduckgo_web_search": {"description": "Search", "parameters": {}},
        "duckduckgo_images": {"description": "Images", "parameters": {}},
        "other_service_tool": {"description": "Other", "parameters": {}},
    }

    class DummyAdapter:
        def __init__(self, tools):
            self._tools = tools

        def get_available_tools(self):
            return self._tools

        def _create_tool_executor(self, tool_name, tool_config):
            async def executor(**kwargs):
                return {"tool": tool_name, "kwargs": kwargs, "description": tool_config.get("description", "")}

            return executor

    @asynccontextmanager
    async def fake_get_mcp_adapter(_gateway_url):
        yield DummyAdapter(available_tools)

    monkeypatch.setattr(base, "get_mcp_adapter", fake_get_mcp_adapter)
    monkeypatch.setattr(
        base,
        "get_settings",
        lambda: types.SimpleNamespace(mcp_gateway_enabled=True, mcp_gateway_url="http://mock"),
    )

    base.clear_mcp_tool_cache()

    try:
        tools = base.get_duckduckgo_tools()
        loaded_names = {tool.name for tool in tools}
        assert loaded_names == {"duckduckgo_web_search", "duckduckgo_images"}
    finally:
        base.clear_mcp_tool_cache()
