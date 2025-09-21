import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Dict, Any
import sys

import httpx
from httpx import Request, Response
import pytest


PYTHON_SERVICE_PATH = Path(__file__).resolve().parents[2] / "python-service"
if str(PYTHON_SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(PYTHON_SERVICE_PATH))

if "python_service" not in sys.modules:
    python_service_pkg = ModuleType("python_service")
    python_service_pkg.__path__ = [str(PYTHON_SERVICE_PATH)]
    sys.modules["python_service"] = python_service_pkg


from python_service.app.services import mcp_adapter as mcp_module  # noqa: E402
from python_service.app.services.mcp_adapter import MCPServerAdapter  # noqa: E402


@pytest.mark.parametrize(
    "redirect_suffix",
    ["/sse?sessionid=abc123", "/sse?sessionId=abc123"],
)
def test_sse_tool_listing_and_execution(monkeypatch, redirect_suffix):
    """The adapter should establish an SSE session and execute DuckDuckGo tools."""

    events: Dict[str, Any] = {}

    @asynccontextmanager
    async def fake_sse_client(url: str, **_: Any):
        events["sse_url"] = url
        try:
            yield ("read_stream", "write_stream")
        finally:
            events["sse_closed"] = True

    class FakeClientSession:
        def __init__(self, read_stream, write_stream):  # type: ignore[no-untyped-def]
            events["client_streams"] = (read_stream, write_stream)

        async def initialize(self):
            events["initialized"] = True

        async def list_tools(self):
            events["listed_tools"] = True
            tool = SimpleNamespace(
                name="web_search",
                description="DuckDuckGo search",
                input_schema={"type": "object"},
            )
            return SimpleNamespace(tools=[tool])

        async def call_tool(self, name: str, arguments: Dict[str, Any]):
            events["call_tool"] = (name, arguments)
            return SimpleNamespace(
                isError=False,
                content=[SimpleNamespace(text="search result")],
            )

    monkeypatch.setattr(
        "python_service.app.services.mcp_adapter.sse_client",
        fake_sse_client,
    )
    monkeypatch.setattr(
        "python_service.app.services.mcp_adapter.ClientSession",
        FakeClientSession,
    )

    async def handler(request: Request) -> Response:
        if request.method == "POST" and request.url.path == "/servers/duckduckgo/connect":
            return Response(307, headers={"location": redirect_suffix})
        if request.method == "POST" and request.url.path == "/servers/duckduckgo/disconnect":
            return Response(200, json={"status": "disconnected"})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    async def run_test() -> None:
        adapter = MCPServerAdapter("http://mock")
        adapter._session = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        await adapter._connect_to_server("duckduckgo", {"transport": "sse"})

        tools = adapter.get_available_tools()
        assert "duckduckgo_web_search" in tools
        connection = adapter._connected_servers["duckduckgo"]
        assert connection["session_id"] == "abc123"
        assert isinstance(connection.get("client"), FakeClientSession)
        expected_sse_url = f"http://mock{redirect_suffix}"
        assert events["sse_url"] == expected_sse_url
        assert events.get("listed_tools")

        result = await adapter.call_tool("duckduckgo_web_search", query="python", max_results=1)
        assert result == "search result"

        called_tool, call_arguments = events["call_tool"]
        assert called_tool == "web_search"
        assert call_arguments["kwargs"]["query"] == "python"
        assert call_arguments["kwargs"]["max_results"] == 1

        await adapter.disconnect()
        assert events.get("sse_closed")

    asyncio.run(run_test())


def test_load_configured_servers_with_container_path(monkeypatch):
    repo_config_path = PYTHON_SERVICE_PATH / "mcp-config" / "servers.json"
    assert repo_config_path.exists(), "Expected servers configuration file to exist in repo"

    monkeypatch.setattr(
        mcp_module,
        "__file__",
        "/app/app/services/mcp_adapter.py",
        raising=False,
    )

    original_open = mcp_module.Path.open
    container_config_path = mcp_module.Path("/app/mcp-config/servers.json")

    def fake_open(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self == container_config_path:
            return original_open(repo_config_path, *args, **kwargs)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(mcp_module.Path, "open", fake_open)

    adapter = MCPServerAdapter()
    servers = adapter._load_configured_servers()

    expected_servers = json.loads(repo_config_path.read_text(encoding="utf-8"))["servers"]

    assert servers == expected_servers
