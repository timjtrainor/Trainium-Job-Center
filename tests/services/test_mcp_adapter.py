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


def test_shared_sse_session_tool_listing_and_execution(monkeypatch):
    """The adapter should reuse a shared SSE session for multiple servers."""

    events: Dict[str, Any] = {
        "connect_calls": [],
        "disconnect_calls": [],
    }

    @asynccontextmanager
    async def fake_sse_client(url: str, **_: Any):
        events.setdefault("sse_urls", []).append(url)
        try:
            yield ("read_stream", "write_stream")
        finally:
            events["sse_closed"] = True

    class FakeClientSession:
        def __init__(self, read_stream, write_stream):  # type: ignore[no-untyped-def]
            events.setdefault("client_streams", []).append((read_stream, write_stream))

        async def initialize(self):
            events["initialize_count"] = events.get("initialize_count", 0) + 1

        async def list_tools(self):
            events["list_tools_count"] = events.get("list_tools_count", 0) + 1
            tool = SimpleNamespace(
                name="web_search",
                description="Shared search tool",
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
    monkeypatch.setattr(
        MCPServerAdapter,
        "_load_configured_servers",
        lambda self: {
            "duckduckgo": {"transport": "sse"},
            "linkedin": {"transport": "sse"},
        },
    )

    async def handler(request: Request) -> Response:
        if request.method == "GET" and request.url.path == "/health":
            return Response(200)
        if request.method == "GET" and request.url.path == "/servers":
            return Response(307, headers={"location": "/sse"})
        if request.method == "POST" and request.url.path == "/sessions":
            events["session_requests"] = events.get("session_requests", 0) + 1
            return Response(200, json={"sessionid": "abc123"})
        if request.method == "POST" and request.url.path in (
            "/servers/duckduckgo/connect",
            "/servers/linkedin/connect",
        ):
            server = request.url.path.split("/")[2]
            events["connect_calls"].append(
                (server, request.url.params.get("sessionid"))
            )
            return Response(200, json={"status": "attached"})
        if request.method == "POST" and request.url.path in (
            "/servers/duckduckgo/disconnect",
            "/servers/linkedin/disconnect",
        ):
            server = request.url.path.split("/")[2]
            payload = json.loads(request.content.decode() or "{}")
            events["disconnect_calls"].append((server, payload))
            return Response(200, json={"status": "disconnected"})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    transport = httpx.MockTransport(handler)
    original_async_client = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs.setdefault("transport", transport)
        kwargs.setdefault("follow_redirects", False)
        return original_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", fake_async_client)

    async def run_test() -> None:
        adapter = MCPServerAdapter("http://mock")
        await adapter.connect()

        tools = adapter.get_available_tools()
        assert set(tools.keys()) == {"duckduckgo_web_search", "linkedin_web_search"}

        connections = adapter._connected_servers
        assert set(connections.keys()) == {"duckduckgo", "linkedin"}
        assert connections["duckduckgo"]["client"] is connections["linkedin"]["client"]
        assert connections["duckduckgo"]["sse_context"] is connections["linkedin"][
            "sse_context"
        ]

        assert events.get("session_requests") == 1
        assert len(events["connect_calls"]) == 2
        assert all(session_id == "abc123" for _, session_id in events["connect_calls"])
        assert events["sse_urls"] == ["http://mock/sse?sessionid=abc123"]
        assert events.get("initialize_count") == 2
        assert events.get("list_tools_count") == 2

        result = await adapter.call_tool(
            "duckduckgo_web_search", query="python", max_results=1
        )
        assert result == "search result"

        called_tool, call_arguments = events["call_tool"]
        assert called_tool == "web_search"
        assert call_arguments["kwargs"]["query"] == "python"
        assert call_arguments["kwargs"]["max_results"] == 1

        await adapter.disconnect()

        assert events.get("sse_closed")
        assert len(events["disconnect_calls"]) == 2
        assert all(
            payload.get("session_id") == "abc123"
            for _, payload in events["disconnect_calls"]
        )

    asyncio.run(run_test())


def test_streamable_http_tool_listing_and_execution(monkeypatch):
    """The adapter should establish a Streamable HTTP session and execute tools."""

    events: Dict[str, Any] = {}

    class FakeHTTPContext:
        def __init__(self):  # type: ignore[no-untyped-def]
            events["http_context_created"] = True

        async def __aenter__(self):
            events["http_entered"] = True

            def get_session_id() -> str:
                events["session_callback_used"] = True
                return events.get("session_id", "abc123")

            events["session_id"] = "abc123"
            return ("read_stream", "write_stream", get_session_id)

        async def __aexit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
            events["http_exited"] = (exc_type, exc)
            return False

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
        "python_service.app.services.mcp_adapter.streamablehttp_client",
        lambda *args, **kwargs: FakeHTTPContext(),
    )
    monkeypatch.setattr(
        "python_service.app.services.mcp_adapter.ClientSession",
        FakeClientSession,
    )

    async def handler(request: Request) -> Response:
        if request.method == "POST" and request.url.path == "/servers/duckduckgo/connect":
            return Response(
                200,
                json={
                    "endpoint": "/stream",
                    "transport": "streamable-http",
                    "session_id": "abc123",
                },
            )
        if request.method == "POST" and request.url.path == "/servers/duckduckgo/disconnect":
            return Response(200, json={"status": "disconnected"})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    async def run_test() -> None:
        adapter = MCPServerAdapter("http://mock")
        adapter._session = httpx.AsyncClient(transport=httpx.MockTransport(handler))

        await adapter._connect_to_server("duckduckgo", {"transport": "streamable-http"})

        connection = adapter._connected_servers["duckduckgo"]
        assert connection["transport"] == "streamable-http"
        assert connection.get("client") is not None
        assert "http_context" in connection
        assert events.get("http_context_created")

        tools = adapter.get_available_tools()
        assert "duckduckgo_web_search" in tools
        assert events.get("http_entered")
        assert events.get("listed_tools")
        assert events.get("session_callback_used")

        result = await adapter.call_tool(
            "duckduckgo_web_search", query="python", max_results=1
        )
        assert result == "search result"

        called_tool, call_arguments = events["call_tool"]
        assert called_tool == "web_search"
        assert call_arguments["kwargs"]["query"] == "python"
        assert call_arguments["kwargs"]["max_results"] == 1

        await adapter.disconnect()
        assert events.get("http_exited")

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
