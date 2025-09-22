import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Dict, Any, Optional, List
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
    "status_code,redirect_suffix,json_payload,set_cookie_headers,response_cookies,expected_session_id,expected_cookie_header",
    [
        (307, "/sse?sessionid=abc123", None, None, None, "abc123", None),
        (307, "/sse?sessionId=abc123", None, None, None, "abc123", None),
        (
            307,
            "/sse",
            None,
            ["sessionId=abc123; Path=/; HttpOnly"],
            None,
            "abc123",
            "sessionId=abc123",
        ),
        (
            307,
            "/sse",
            None,
            [
                "sessionId=abc123; Path=/; HttpOnly",
                "sessionId.sig=xyz789; Path=/; HttpOnly",
            ],
            None,
            "abc123",
            "sessionId=abc123; sessionId.sig=xyz789",
        ),
        (
            200,
            "/sse",
            {"endpoint": "/sse"},
            ["sessionId=abc123; Path=/; HttpOnly"],
            None,
            "abc123",
            "sessionId=abc123",
        ),
        pytest.param(
            307,
            "/sse",
            None,
            None,
            {"sessionId": "abc123", "sessionId.sig": "xyz789"},
            "abc123",
            "sessionId=abc123; sessionId.sig=xyz789",
            id="cookies-from-response-jar",
        ),
    ],
)
def test_sse_tool_listing_and_execution(
    monkeypatch,
    status_code,
    redirect_suffix,
    json_payload,
    set_cookie_headers,
    response_cookies,
    expected_session_id,
    expected_cookie_header,
):
    """The adapter should establish an SSE session and execute DuckDuckGo tools."""

    events: Dict[str, Any] = {}

    def split_cookie_header(value: Optional[str]) -> List[str]:
        if not value:
            return []
        return sorted(part.strip() for part in value.split(";") if part.strip())

    @asynccontextmanager
    async def fake_sse_client(
        url: str, headers: Optional[Dict[str, Any]] = None, **_: Any
    ):
        events["sse_url"] = url
        events["sse_headers"] = headers
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
            response_headers = []
            if set_cookie_headers:
                response_headers.extend(
                    ("set-cookie", header_value) for header_value in set_cookie_headers
                )
            if status_code == 307:
                response_headers.append(("location", redirect_suffix))
            elif status_code == 200:
                assert (
                    json_payload is not None
                ), "JSON payload must be provided for 200 responses"
            else:
                raise AssertionError(f"Unsupported status code for test: {status_code}")

            response_kwargs: Dict[str, Any] = {"headers": response_headers}
            if status_code == 200 and json_payload is not None:
                response_kwargs["json"] = json_payload

            response = Response(status_code, request=request, **response_kwargs)
            if response_cookies:
                for name, value in response_cookies.items():
                    response.cookies.set(name, value)

            return response
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
        assert connection["session_id"] == expected_session_id
        actual_connection_cookie = connection.get("session_cookie")
        if expected_cookie_header:
            assert split_cookie_header(actual_connection_cookie) == split_cookie_header(
                expected_cookie_header
            )
        else:
            assert actual_connection_cookie in (None, "")
        assert isinstance(connection.get("client"), FakeClientSession)
        expected_sse_url = f"http://mock{redirect_suffix}"
        assert events["sse_url"] == expected_sse_url
        sse_headers = events.get("sse_headers")
        if expected_cookie_header:
            assert sse_headers is not None
            assert split_cookie_header(sse_headers.get("Cookie")) == split_cookie_header(
                expected_cookie_header
            )
        else:
            assert not sse_headers or "Cookie" not in sse_headers
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
