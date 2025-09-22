"""MCP Server Adapter for integrating with Docker MCP Gateway."""

import asyncio
import inspect
import json
import socket
from collections import OrderedDict
from contextlib import asynccontextmanager, suppress
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from loguru import logger

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import Tool as MCPTool


DEFAULT_FALLBACK_TOOLS: Dict[str, List[Dict[str, Any]]] = {
    "duckduckgo": [
        {
            "name": "web_search",
            "description": "Perform a DuckDuckGo web search when dynamic tool discovery fails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text to send to DuckDuckGo.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return.",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }
    ]
}


class MCPServerAdapter:
    """
    Adapter for connecting to Docker MCP Gateway and managing MCP servers.
    
    This adapter provides context management for MCP connections and tools
    that can be injected into CrewAI agents.
    """
    
    def __init__(self, gateway_url: str = "http://localhost:8811"):
        """
        Initialize the MCP Server Adapter.
        
        Args:
            gateway_url: URL of the Docker MCP Gateway
        """
        self.gateway_url = gateway_url.rstrip('/')
        self._session: Optional[httpx.AsyncClient] = None
        self._connected_servers: Dict[str, Any] = {}
        self._available_tools: Dict[str, MCPTool] = {}
        self._discovery_timeout: float = 30.0
        self._http_connect_timeout: float = 30.0
        self._http_stream_read_timeout: float = 300.0
        self._server_configs: Dict[str, Dict[str, Any]] = {}

    def _load_configured_servers(self) -> Dict[str, Dict[str, Any]]:
        """Load MCP server definitions from configuration."""
        module_path = Path(__file__).resolve()
        python_service_root = module_path.parents[2]

        candidate_paths = [python_service_root / "mcp-config" / "servers.json"]

        container_config_path = Path("/app") / "mcp-config" / "servers.json"
        if container_config_path not in candidate_paths:
            candidate_paths.append(container_config_path)

        for config_path in candidate_paths:
            try:
                with config_path.open("r", encoding="utf-8") as config_file:
                    config_data = json.load(config_file)

                servers = config_data.get("servers", {})
                if isinstance(servers, dict):
                    return servers

                logger.warning(
                    f"Invalid servers configuration structure in {config_path}: expected a mapping"
                )
            except FileNotFoundError:
                logger.warning(
                    f"Servers configuration file not found at {config_path}."
                )
            except json.JSONDecodeError as exc:
                logger.warning(
                    f"Failed to parse servers configuration at {config_path}: {exc}"
                )
            except Exception as exc:
                logger.warning(
                    f"Unexpected error loading servers configuration from {config_path}: {exc}"
                )

        return {}
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self) -> None:
        """Connect to the MCP Gateway and initialize servers."""
        try:
            # Don't follow redirects automatically to handle SSE properly
            timeout = httpx.Timeout(self._http_connect_timeout)
            self._session = httpx.AsyncClient(timeout=timeout, follow_redirects=False)
            self._server_configs.clear()

            # Check gateway health
            response = await self._session.get(f"{self.gateway_url}/health")
            response.raise_for_status()
            
            # For SSE transport, the /servers endpoint redirects to /sse
            # We need to handle this manually to avoid timeout issues
            servers_response = await self._session.get(f"{self.gateway_url}/servers")
            
            if servers_response.status_code == 307:
                # Handle redirect for SSE transport
                redirect_location = servers_response.headers.get("location", "/sse")
                if redirect_location.startswith("/"):
                    redirect_url = f"{self.gateway_url}{redirect_location}"
                else:
                    redirect_url = redirect_location

                logger.info(f"MCP Gateway using SSE transport, endpoint: {redirect_url}")

                configured_servers = self._load_configured_servers()
                if configured_servers:
                    servers_data = {}
                    for server_name, server_details in configured_servers.items():
                        merged_details = dict(server_details)
                        merged_details["transport"] = "sse"
                        merged_details["endpoint"] = redirect_url
                        servers_data[server_name] = merged_details
                else:
                    logger.warning(
                        "No configured MCP servers found; defaulting to DuckDuckGo for SSE transport"
                    )
                    servers_data = {
                        "duckduckgo": {"transport": "sse", "endpoint": redirect_url}
                    }
            else:
                servers_response.raise_for_status()
                servers_data = servers_response.json()
            
            server_names = list(servers_data.keys())
            if not server_names:
                logger.warning("MCP Gateway returned no configured servers")
                return

            logger.info(
                "MCP Gateway connected. Available servers: {}".format(server_names)
            )

            # Connect to each server and retrieve tools
            for server_name, server_config in servers_data.items():
                await self._connect_to_server(server_name, server_config)

        except Exception as e:
            logger.error(f"Failed to connect to MCP Gateway: {e}")
            try:
                diagnostics = await self._diagnose_gateway_connectivity()
                logger.error("MCP Gateway diagnostics: {}", diagnostics)
            except Exception as diag_exc:
                logger.warning(
                    f"Gateway diagnostics failed during connection error analysis: {diag_exc}"
                )
            if self._session:
                await self._session.aclose()
                self._session = None
            raise

    async def _diagnose_gateway_connectivity(self) -> Dict[str, Any]:
        """Diagnose gateway connectivity and return detailed status."""

        diagnostics: Dict[str, Any] = {
            "gateway_url": self.gateway_url,
            "health_check": False,
            "servers_endpoint": False,
            "network_reachable": False,
            "response_times": {},
            "errors": [],
            "available_servers": [],
        }

        parsed_url = urlparse(self.gateway_url)
        host = parsed_url.hostname or parsed_url.path

        if not host:
            diagnostics["errors"].append(
                "Invalid gateway URL: unable to determine host component"
            )
            return diagnostics

        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

        try:
            with socket.create_connection((host, port), timeout=5):
                diagnostics["network_reachable"] = True
        except OSError as exc:
            diagnostics["errors"].append(f"Cannot reach {host}:{port} - {exc}")
            return diagnostics
        except Exception as exc:
            diagnostics["errors"].append(f"Network test failed: {exc}")
            return diagnostics

        session: Optional[httpx.AsyncClient] = self._session
        created_session = False

        try:
            if session is None or getattr(session, "is_closed", False):
                timeout = httpx.Timeout(self._http_connect_timeout)
                session = httpx.AsyncClient(timeout=timeout, follow_redirects=False)
                created_session = True

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()

            # Health endpoint diagnostics
            try:
                start_time = loop.time()
                response = await session.get(
                    f"{self.gateway_url}/health", timeout=10.0
                )
                diagnostics["response_times"]["health"] = loop.time() - start_time
                diagnostics["health_check"] = response.status_code == 200

                if response.status_code != 200:
                    diagnostics["errors"].append(
                        f"Health check failed: {response.status_code} - {response.text}"
                    )
            except Exception as exc:
                diagnostics["errors"].append(f"Health check error: {exc}")

            # Servers endpoint diagnostics
            try:
                start_time = loop.time()
                response = await session.get(
                    f"{self.gateway_url}/servers", timeout=10.0
                )
                diagnostics["response_times"]["servers"] = loop.time() - start_time

                if response.status_code in {200, 307}:
                    diagnostics["servers_endpoint"] = True
                else:
                    diagnostics["errors"].append(
                        f"Servers endpoint failed: {response.status_code} - {response.text}"
                    )

                if response.status_code == 200:
                    try:
                        servers_data = response.json()
                        if isinstance(servers_data, dict):
                            diagnostics["available_servers"] = list(servers_data.keys())
                        else:
                            diagnostics["errors"].append(
                                "Servers endpoint returned unexpected payload format"
                            )
                    except Exception as exc:
                        diagnostics["errors"].append(
                            f"Failed to parse servers response: {exc}"
                        )
                elif response.status_code == 307:
                    diagnostics["sse_redirect"] = response.headers.get("location")
            except Exception as exc:
                diagnostics["errors"].append(f"Servers endpoint error: {exc}")
        finally:
            if created_session and session is not None:
                await session.aclose()

        return diagnostics

    async def get_gateway_diagnostics(self) -> Dict[str, Any]:
        """Public helper for gathering gateway diagnostic information."""

        return await self._diagnose_gateway_connectivity()

    async def disconnect(self) -> None:
        """Disconnect from the MCP Gateway and clean up."""
        if self._session:
            try:
                # Disconnect from all servers
                for server_name in list(self._connected_servers.keys()):
                    await self._disconnect_from_server(server_name)
                    
                await self._session.aclose()
            except Exception as e:
                logger.warning(f"Error during MCP Gateway disconnect: {e}")
            finally:
                self._session = None
                self._connected_servers.clear()
                self._available_tools.clear()
                
    async def _connect_to_server(self, server_name: str, server_config: Dict[str, Any]) -> None:
        """Connect to a specific MCP server through the gateway."""
        try:
            if not self._session:
                raise RuntimeError("HTTP session is not initialized")

            allow_rest_fallback = bool(
                server_config.get("allow_rest_fallback")
                or server_config.get("options", {}).get("allow_rest_fallback")
            )

            self._server_configs[server_name] = {
                "config": dict(server_config),
                "allow_rest_fallback": allow_rest_fallback,
            }

            logger.info(f"Connecting to MCP server '{server_name}'...")

            connect_response = await self._session.post(
                f"{self.gateway_url}/servers/{server_name}/connect",
                follow_redirects=False,
                timeout=10.0,
            )

            logger.debug(f"Connect response for {server_name}: {connect_response.status_code}")

            # Handle SSE transport (307 redirect or 200 with endpoint)
            if (
                str(server_config.get("transport", "")).lower() == "sse"
                or connect_response.status_code == 307
                or (connect_response.status_code == 200 and self._response_contains_sse_endpoint(connect_response))
            ):
                logger.debug(f"Using SSE transport for server '{server_name}'")
                await self._connect_to_server_via_sse(
                    server_name,
                    server_config,
                    connect_response,
                    allow_rest_fallback=allow_rest_fallback,
                )
                return

            # Handle other transport types
            connect_response.raise_for_status()

            payload: Dict[str, Any] = {}
            try:
                payload = connect_response.json()
                if not isinstance(payload, dict):
                    payload = {}
            except ValueError as exc:
                logger.warning(
                    f"Gateway returned non-JSON response when connecting to '{server_name}': {exc}"
                )

            transport_hint = str(
                payload.get("transport")
                or server_config.get("transport")
                or ""
            ).lower()

            endpoint_hint = (
                payload.get("endpoint")
                or payload.get("url")
                or payload.get("connection_url")
                or server_config.get("endpoint")
            )

            headers_hint = payload.get("headers")
            if not isinstance(headers_hint, dict):
                headers_hint = None

            session_id = payload.get("session_id") if isinstance(payload, dict) else None

            endpoint_url: Optional[str] = None
            if isinstance(endpoint_hint, str) and endpoint_hint:
                endpoint_url = (
                    urljoin(f"{self.gateway_url}/", endpoint_hint.lstrip("/"))
                    if endpoint_hint.startswith("/")
                    else endpoint_hint
                )

            if transport_hint in {"streamable-http", "http"} or endpoint_url:
                logger.debug(f"Using Streamable HTTP transport for server '{server_name}'")
                await self._connect_to_server_via_streamable_http(
                    server_name,
                    server_config,
                    endpoint_url,
                    headers=headers_hint,
                    initial_session_id=session_id,
                    allow_rest_fallback=allow_rest_fallback,
                )
                return

            if allow_rest_fallback and session_id:
                logger.warning(
                    f"Server '{server_name}' did not expose a protocol endpoint; enabling REST fallback for execution"
                )
                self._connected_servers[server_name] = {
                    "config": server_config,
                    "session_id": session_id,
                    "transport": "rest",
                    "rest_fallback": True,
                }
                logger.warning(
                    f"No MCP tools registered for server '{server_name}' (REST fallback mode)"
                )
                return

            logger.error(f"Unable to determine transport endpoint for server '{server_name}'. Response: {payload}")
            raise ValueError(
                f"Unable to determine transport endpoint for server '{server_name}'"
            )

        except asyncio.TimeoutError as exc:
            metadata = self._server_configs.setdefault(server_name, {})
            metadata["error"] = f"Timeout loading tools for {server_name}: {exc}"
            metadata["last_failure"] = "timeout"
            logger.warning(f"Timeout loading tools for {server_name}, using defaults")
            await self._load_default_tools(server_name)
        except httpx.HTTPStatusError as e:
            metadata = self._server_configs.setdefault(server_name, {})
            metadata["error"] = (
                f"HTTP error loading tools for {server_name}: {e.response.status_code} - {e.response.text}"
            )
            metadata["last_failure"] = "http_status"
            logger.error(
                f"HTTP error loading tools for {server_name}: {e.response.status_code} - {e.response.text}"
            )
            await self._load_default_tools(server_name)
        except httpx.RequestError as e:
            metadata = self._server_configs.setdefault(server_name, {})
            metadata["error"] = (
                f"Request error loading tools for {server_name}: {type(e).__name__} - {str(e)}"
            )
            metadata["last_failure"] = "request"
            logger.error(
                f"Request error loading tools for {server_name}: {type(e).__name__} - {str(e)}"
            )
            await self._load_default_tools(server_name)
        except Exception as e:
            metadata = self._server_configs.setdefault(server_name, {})
            metadata["error"] = (
                f"Unexpected error loading tools for {server_name}: {type(e).__name__} - {str(e)}"
            )
            metadata["last_failure"] = type(e).__name__
            logger.error(
                f"Unexpected error loading tools for {server_name}: {type(e).__name__} - {str(e)}"
            )
            logger.exception("Full traceback:")
            await self._load_default_tools(server_name)

    async def _load_default_tools(self, server_name: str) -> None:
        """Load statically defined fallback tools when dynamic discovery fails."""

        server_state = self._server_configs.get(server_name, {})
        server_config = dict(server_state.get("config", {}))
        allow_rest_fallback = bool(server_state.get("allow_rest_fallback"))
        failure_message = server_state.get("error") or "Default tool fallback engaged"

        # Remove any stale tool registrations for this server
        tools_to_remove = [
            tool_name
            for tool_name in list(self._available_tools.keys())
            if tool_name.startswith(f"{server_name}_")
        ]
        for tool_name in tools_to_remove:
            del self._available_tools[tool_name]

        # Mark connection as failed but keep metadata for debugging
        self._connected_servers[server_name] = {
            "config": server_config,
            "session_id": f"failed_session_{server_name}",
            "transport": "failed",
            "error": failure_message,
            "rest_fallback": allow_rest_fallback,
        }

        fallback_tools = DEFAULT_FALLBACK_TOOLS.get(server_name.lower())
        if not fallback_tools:
            logger.warning(
                f"No default tool definitions available for server '{server_name}'."
            )
            return

        for tool in fallback_tools:
            normalized_tool = self._normalize_tool(tool)
            normalized_tool["server"] = server_name
            self._available_tools[f"{server_name}_{normalized_tool['name']}"] = normalized_tool

        logger.info(
            f"Loaded {len(fallback_tools)} default tools for server '{server_name}'"
        )

    def _response_contains_sse_endpoint(self, response: httpx.Response) -> bool:
        """Check if a 200 response contains an SSE endpoint."""
        try:
            if response.status_code != 200:
                return False
            
            payload = response.json()
            endpoint = payload.get("endpoint", "")
            
            # Check if endpoint contains SSE indicators
            return "/sse" in str(endpoint) or "sse" in str(payload.get("transport", "")).lower()
        except (ValueError, KeyError):
            return False

    async def _initialize_and_register_tools(
        self, server_name: str, client_handle: ClientSession
    ) -> int:
        """Initialize a client session and register discovered tools."""

        try:
            await asyncio.wait_for(
                client_handle.initialize(), timeout=self._discovery_timeout
            )
        except asyncio.TimeoutError as exc:
            raise TimeoutError(
                f"Timed out initializing server '{server_name}' after {self._discovery_timeout} seconds"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize MCP server '{server_name}': {exc}"
            ) from exc

        try:
            tools_result = await asyncio.wait_for(
                client_handle.list_tools(), timeout=self._discovery_timeout
            )
        except asyncio.TimeoutError as exc:
            raise TimeoutError(
                f"Timed out listing tools for server '{server_name}' after {self._discovery_timeout} seconds"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Failed to list tools for server '{server_name}': {exc}"
            ) from exc

        raw_tools = getattr(tools_result, "tools", None) or []
        tool_count = self._register_tools(server_name, raw_tools)

        if tool_count:
            logger.info(
                f"Discovered {tool_count} tools for server '{server_name}' via MCP protocol"
            )
        else:
            logger.warning(
                f"No tools reported by server '{server_name}' during MCP discovery"
            )

        return tool_count

    async def _connect_to_server_via_streamable_http(
        self,
        server_name: str,
        server_config: Dict[str, Any],
        endpoint_url: Optional[str],
        *,
        headers: Optional[Dict[str, str]] = None,
        initial_session_id: Optional[str] = None,
        allow_rest_fallback: bool = False,
    ) -> None:
        """Establish a Streamable HTTP connection and discover tools via MCP."""

        if not endpoint_url:
            if allow_rest_fallback and initial_session_id:
                logger.warning(
                    f"Server '{server_name}' did not provide a Streamable HTTP endpoint; falling back to REST execution"
                )
                self._connected_servers[server_name] = {
                    "config": server_config,
                    "session_id": initial_session_id,
                    "transport": "rest",
                    "rest_fallback": True,
                }
                logger.warning(
                    f"No MCP tools registered for server '{server_name}' (REST fallback mode)"
                )
                return

            raise ValueError(
                f"Server '{server_name}' did not provide a Streamable HTTP endpoint"
            )

        http_context = streamablehttp_client(
            endpoint_url,
            headers=headers,
            timeout=self._http_connect_timeout,
            sse_read_timeout=self._http_stream_read_timeout,
        )

        client_handle: Optional[ClientSession] = None
        session_identifier = initial_session_id

        try:
            read_stream, write_stream, get_session_id = await http_context.__aenter__()
            client_handle = ClientSession(read_stream, write_stream)
            await self._initialize_and_register_tools(server_name, client_handle)

            try:
                resolved_session = get_session_id()
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.debug(
                    f"Failed to retrieve session identifier for '{server_name}' via HTTP transport: {exc}"
                )
            else:
                if resolved_session:
                    session_identifier = resolved_session

            if hasattr(client_handle, "list_resources"):
                try:
                    resources_result = await client_handle.list_resources()
                except Exception as resources_exc:  # pragma: no cover - optional capability
                    logger.debug(
                        f"Resource discovery not available for {server_name}: {resources_exc}"
                    )
                else:
                    resources = getattr(resources_result, "resources", None) or []
                    if resources:
                        logger.info(
                            f"Discovered {len(resources)} resources for {server_name}"
                        )

        except Exception as exc:
            with suppress(Exception):
                await http_context.__aexit__(type(exc), exc, exc.__traceback__)
            raise

        if not session_identifier:
            session_identifier = f"http_session_{server_name}"
            logger.debug(
                f"No session identifier provided for '{server_name}'; generated '{session_identifier}'"
            )

        self._connected_servers[server_name] = {
            "config": server_config,
            "session_id": session_identifier,
            "transport": "streamable-http",
            "client": client_handle,
            "http_context": http_context,
            "rest_fallback": allow_rest_fallback,
        }

        logger.info(
            f"Connected to MCP server '{server_name}' via Streamable HTTP transport"
        )

    async def _connect_to_server_via_sse(
        self,
        server_name: str,
        server_config: Dict[str, Any],
        connect_response: httpx.Response,
        *,
        allow_rest_fallback: bool = False,
    ) -> None:
        """Establish an SSE connection and discover tools via MCP protocol."""

        session_id: Optional[str] = None
        redirect_url: Optional[str] = None
        session_cookie_header: Optional[str] = None
        cookie_session_id: Optional[str] = None

        # Handle session cookies if present (may also contain the session id)
        cookie_values: "OrderedDict[str, str]" = OrderedDict()

        # Gather cookies directly from Set-Cookie headers to preserve server ordering.
        raw_set_cookie_headers: List[str] = []
        headers_obj = getattr(connect_response, "headers", None)
        if headers_obj is not None:
            if hasattr(headers_obj, "get_list"):
                raw_set_cookie_headers = list(headers_obj.get_list("set-cookie"))
            else:
                header_value = headers_obj.get("set-cookie")
                if header_value:
                    raw_set_cookie_headers = [header_value]

        for header_value in raw_set_cookie_headers:
            cookie_jar = SimpleCookie()
            try:
                cookie_jar.load(header_value)
            except Exception as exc:
                logger.warning(
                    f"Failed to parse session cookie for server '{server_name}': {exc}"
                )
                continue

            for morsel in cookie_jar.values():
                cookie_name = (morsel.key or "").strip()
                cookie_value = morsel.value
                if not cookie_name:
                    continue

                cookie_values[cookie_name] = cookie_value
                if cookie_name.lower() == "sessionid" and cookie_value:
                    cookie_session_id = cookie_value

        # Merge cookies tracked by httpx on the response object to cover cases where
        # middleware consolidates Set-Cookie headers.
        try:
            response_cookies = getattr(connect_response, "cookies", None)
            cookie_jar_obj = (
                getattr(response_cookies, "jar", None)
                if response_cookies is not None
                else None
            )
            if cookie_jar_obj:
                for cookie in cookie_jar_obj:
                    cookie_name = getattr(cookie, "name", "").strip()
                    cookie_value = getattr(cookie, "value", "")
                    if not cookie_name:
                        continue

                    cookie_values[cookie_name] = cookie_value
                    if cookie_name.lower() == "sessionid" and cookie_value:
                        cookie_session_id = cookie_value
        except Exception as exc:
            logger.debug(
                f"Failed to inspect response cookie jar for server '{server_name}': {exc}"
            )

        if cookie_values:
            session_cookie_header = "; ".join(
                f"{name}={value}" for name, value in cookie_values.items()
            )
            logger.debug(
                f"Using session cookies for {server_name}: {session_cookie_header}"
            )

        # Handle 307 Temporary Redirect
        if connect_response.status_code == 307:
            if "location" not in connect_response.headers:
                raise ValueError(
                    f"Missing redirect location for SSE server '{server_name}'"
                )

            redirect_location = connect_response.headers["location"]
            redirect_url = urljoin(f"{self.gateway_url}/", redirect_location)
            
            logger.info(f"Received 307 redirect for {server_name} to: {redirect_url}")

            # Extract sessionid from redirect URL
            parsed = urlparse(redirect_url)
            query_params = parse_qs(parsed.query)
            normalized_query = {key.lower(): value for key, value in query_params.items()}
            session_id_from_query = normalized_query.get("sessionid", [None])[0]
            if (
                session_id_from_query
                and cookie_session_id
                and session_id_from_query != cookie_session_id
            ):
                logger.warning(
                    "Session ID mismatch between redirect query and cookies for "
                    f"server '{server_name}'. Preferring the redirect query value."
                )

            session_id_candidate = session_id_from_query or cookie_session_id

            if session_id_from_query:
                logger.debug(
                    f"Using sessionid from redirect query for server '{server_name}'"
                )
            elif cookie_session_id:
                logger.debug(
                    f"Using sessionid from session cookies for server '{server_name}'"
                )

            if session_id_candidate:
                session_id = session_id_candidate
            else:
                cookie_names = ", ".join(cookie_values.keys()) if cookie_values else "none"
                logger.error(
                    f"Missing sessionid for server '{server_name}' after redirect; cookie names: {cookie_names}"
                )
                if allow_rest_fallback:
                    logger.warning(
                        f"Falling back to REST for server '{server_name}' due to missing sessionid"
                    )
                    session_id = f"fallback_session_{server_name}"
                    self._connected_servers[server_name] = {
                        "config": server_config,
                        "session_id": session_id,
                        "transport": "rest",
                        "rest_fallback": True,
                    }
                    return
                raise ValueError(
                    f"Missing sessionid in redirect for server '{server_name}'"
                )

        # Handle 200 OK with JSON endpoint
        elif connect_response.status_code == 200:
            try:
                payload = connect_response.json()
                endpoint = payload.get("endpoint")
                
                if not endpoint:
                    raise ValueError(f"Missing endpoint in JSON response for server '{server_name}'")
                
                redirect_url = urljoin(f"{self.gateway_url}/", endpoint.lstrip("/")) if endpoint.startswith("/") else endpoint
                logger.info(f"Received JSON endpoint for {server_name}: {redirect_url}")

                # Extract sessionid from endpoint URL
                parsed = urlparse(redirect_url)
                query_params = parse_qs(parsed.query)
                normalized_query = {key.lower(): value for key, value in query_params.items()}
                session_id_from_query = normalized_query.get("sessionid", [None])[0]
                if (
                    session_id_from_query
                    and cookie_session_id
                    and session_id_from_query != cookie_session_id
                ):
                    logger.warning(
                        "Session ID mismatch between endpoint query and cookies for "
                        f"server '{server_name}'. Preferring the endpoint value."
                    )

                session_id_candidate = session_id_from_query or cookie_session_id

                if session_id_from_query:
                    logger.debug(
                        f"Using sessionid from endpoint query for server '{server_name}'"
                    )
                elif cookie_session_id:
                    logger.debug(
                        f"Using sessionid from session cookies for server '{server_name}'"
                    )

                if session_id_candidate:
                    session_id = session_id_candidate
                else:
                    cookie_names = ", ".join(cookie_values.keys()) if cookie_values else "none"
                    logger.error(
                        f"Missing sessionid for server '{server_name}' after JSON endpoint; cookie names: {cookie_names}"
                    )
                    if allow_rest_fallback:
                        logger.warning(
                            f"Falling back to REST for server '{server_name}' due to missing sessionid"
                        )
                        session_id = f"fallback_session_{server_name}"
                        self._connected_servers[server_name] = {
                            "config": server_config,
                            "session_id": session_id,
                            "transport": "rest",
                            "rest_fallback": True,
                        }
                        return
                    raise ValueError(
                        f"Missing sessionid in endpoint for server '{server_name}'"
                    )

            except (ValueError, KeyError) as e:
                logger.error(f"Failed to parse JSON response for server '{server_name}': {e}")
                raise ValueError(f"Invalid JSON response from gateway for server '{server_name}': {e}")

        else:
            connect_response.raise_for_status()
            raise ValueError(f"Unexpected response status {connect_response.status_code} for SSE server '{server_name}'")

        # Ensure we have valid session ID and redirect URL
        if session_id is None or not redirect_url:
            raise ValueError(f"Missing session ID or redirect URL for server '{server_name}'")

        logger.info(f"Establishing SSE session for {server_name} at {redirect_url} with session ID: {session_id}")

        # Prepare SSE headers
        sse_headers = {"Cookie": session_cookie_header} if session_cookie_header else None

        # Create SSE connection with proper error handling and timeouts
        sse_context = sse_client(redirect_url, headers=sse_headers)
        client_handle: Optional[ClientSession] = None
        tool_count = 0

        try:
            # Add timeout protection for SSE connection establishment
            logger.debug(f"Opening SSE connection to {redirect_url}...")
            
            async def _establish_sse_connection():
                return await sse_context.__aenter__()
            
            # Use asyncio.wait_for to add timeout protection
            read_stream, write_stream = await asyncio.wait_for(
                _establish_sse_connection(),
                timeout=30.0  # 30 second timeout for SSE connection
            )
            
            logger.debug(f"SSE connection established for {server_name}, initializing client session...")
            
            client_handle = ClientSession(read_stream, write_stream)
            
            # Add timeout protection for initialization and tool discovery
            tool_count = await asyncio.wait_for(
                self._initialize_and_register_tools(server_name, client_handle),
                timeout=60.0  # 60 second timeout for tool discovery
            )

            # Optional: Try to discover resources if available
            if hasattr(client_handle, "list_resources"):
                try:
                    resources_result = await asyncio.wait_for(
                        client_handle.list_resources(),
                        timeout=30.0
                    )
                    resources = getattr(resources_result, "resources", None) or []
                    if resources:
                        logger.info(f"Discovered {len(resources)} resources for {server_name}")
                except asyncio.TimeoutError:
                    logger.warning(f"Resource discovery timed out for {server_name}")
                except Exception as resources_exc:
                    logger.debug(f"Resource discovery not available for {server_name}: {resources_exc}")

        except asyncio.TimeoutError as exc:
            logger.error(f"Timeout establishing SSE connection or discovering tools for server '{server_name}': {exc}")
            # Clean up SSE context
            with suppress(Exception):
                await sse_context.__aexit__(type(exc), exc, exc.__traceback__)
            
            if allow_rest_fallback:
                logger.warning(f"Falling back to REST for server '{server_name}' due to SSE timeout")
                self._connected_servers[server_name] = {
                    "config": server_config,
                    "session_id": session_id,
                    "transport": "rest",
                    "rest_fallback": True,
                }
                return
            else:
                raise TimeoutError(f"SSE connection timeout for server '{server_name}'") from exc

        except Exception as exc:
            logger.error(f"Failed to establish SSE connection for server '{server_name}': {exc}")
            # Clean up SSE context
            with suppress(Exception):
                await sse_context.__aexit__(type(exc), exc, exc.__traceback__)
            raise

        # Store successful connection
        self._connected_servers[server_name] = {
            "config": server_config,
            "session_id": session_id,
            "session_cookie": session_cookie_header,
            "transport": "sse",
            "client": client_handle,
            "sse_context": sse_context,
            "rest_fallback": allow_rest_fallback,
        }

        logger.info(
            f"Successfully connected to MCP server '{server_name}' via SSE transport (session {session_id}, {tool_count} tools)"
        )

    def _register_tools(self, server_name: str, tools: Iterable[Any]) -> int:
        """Normalize and register tools for a server."""
        count = 0

        for raw_tool in tools:
            normalized_tool = self._normalize_tool(raw_tool)
            tool_name = normalized_tool.get("name")

            if not tool_name:
                logger.warning(
                    f"Skipping tool without name from server '{server_name}'"
                )
                continue

            stored_tool = dict(normalized_tool)
            stored_tool["server"] = server_name
            self._available_tools[f"{server_name}_{tool_name}"] = stored_tool
            count += 1

        return count

    def _normalize_tool(self, tool: Union[Dict[str, Any], MCPTool, Any]) -> Dict[str, Any]:
        """Convert a tool definition into a consistent dictionary structure."""
        if isinstance(tool, dict):
            parameters = tool.get("parameters")
            if not isinstance(parameters, dict):
                parameters = tool.get("input_schema") if isinstance(tool.get("input_schema"), dict) else {}
            return {
                "name": tool.get("name"),
                "description": tool.get("description", "") or "",
                "parameters": parameters or {},
            }

        name = getattr(tool, "name", None)
        description = getattr(tool, "description", "") or ""

        parameters: Any = getattr(tool, "parameters", None)
        if not isinstance(parameters, dict):
            parameters = getattr(tool, "input_schema", {})

        if hasattr(tool, "model_dump"):
            try:
                dumped = tool.model_dump(by_alias=False, exclude_none=True)
            except TypeError:
                dumped = tool.model_dump()

            name = dumped.get("name", name)
            description = dumped.get("description", description) or ""
            dumped_parameters = dumped.get("parameters") or dumped.get("input_schema")
            if isinstance(dumped_parameters, dict):
                parameters = dumped_parameters

        if not isinstance(parameters, dict):
            parameters = {}

        return {
            "name": name,
            "description": description,
            "parameters": parameters,
        }

    async def _disconnect_from_server(self, server_name: str) -> None:
        """Disconnect from a specific MCP server."""
        if server_name in self._connected_servers:
            try:
                connection_info = self._connected_servers[server_name]
                session_id = connection_info.get("session_id")

                sse_context = connection_info.get("sse_context")
                if sse_context:
                    try:
                        await sse_context.__aexit__(None, None, None)
                    except Exception as exc:
                        logger.warning(
                            f"Error closing SSE stream for server '{server_name}': {exc}"
                        )

                http_context = connection_info.get("http_context")
                if http_context:
                    try:
                        await http_context.__aexit__(None, None, None)
                    except Exception as exc:
                        logger.warning(
                            f"Error closing Streamable HTTP session for server '{server_name}': {exc}"
                        )

                client_handle = connection_info.get("client")
                if client_handle and hasattr(client_handle, "close"):
                    try:
                        close_result = client_handle.close()
                        if inspect.isawaitable(close_result):
                            await close_result
                    except Exception as exc:
                        logger.warning(
                            f"Error closing client session for server '{server_name}': {exc}"
                        )

                if session_id:
                    await self._session.post(
                        f"{self.gateway_url}/servers/{server_name}/disconnect",
                        json={"session_id": session_id}
                    )
                    
                # Remove tools from this server
                tools_to_remove = [
                    tool_name for tool_name in self._available_tools.keys()
                    if tool_name.startswith(f"{server_name}_")
                ]
                for tool_name in tools_to_remove:
                    del self._available_tools[tool_name]

                del self._connected_servers[server_name]
                self._server_configs.pop(server_name, None)
                logger.info(f"Disconnected from MCP server '{server_name}'")

            except Exception as e:
                logger.warning(f"Error disconnecting from MCP server '{server_name}': {e}")
                
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available tools from connected MCP servers.

        Returns:
            Dictionary of tool name to tool configuration
        """
        return dict(self._available_tools)

    def get_available_servers(self) -> List[str]:
        """Return the list of connected MCP servers."""
        return list(self._connected_servers.keys())
        
    def get_duckduckgo_tools(self) -> List[Dict[str, Any]]:
        """
        Get DuckDuckGo-specific tools for injection into CrewAI agents.
        
        Returns:
            List of tool configurations compatible with CrewAI
        """
        duckduckgo_tools = []
        
        for tool_name, tool_config in self._available_tools.items():
            if tool_name.startswith("duckduckgo_"):
                # Convert MCP tool format to CrewAI tool format
                crewai_tool = self._convert_mcp_tool_to_crewai(tool_name, tool_config)
                duckduckgo_tools.append(crewai_tool)

        return duckduckgo_tools
                
    def get_linkedin_tools(self) -> List[Dict[str, Any]]:
        """
        Get LinkedIn-specific tools for injection into CrewAI agents.
        
        Returns:
            List of tool configurations compatible with CrewAI
        """
        linkedin_tools = []
        
        for tool_name, tool_config in self._available_tools.items():
            if "linkedin" in tool_name.lower():
                # Convert MCP tool format to CrewAI tool format
                crewai_tool = self._convert_mcp_tool_to_crewai(tool_name, tool_config)
                linkedin_tools.append(crewai_tool)
                
        return linkedin_tools
        
    def _convert_mcp_tool_to_crewai(self, tool_name: str, mcp_tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MCP tool format to CrewAI-compatible tool format.

        Args:
            tool_name: Name of the tool
            mcp_tool: MCP tool configuration

        Returns:
            CrewAI-compatible tool configuration
        """
        return {
            "name": tool_name,
            "description": mcp_tool.get("description", ""),
            "parameters": mcp_tool.get("parameters", {}),
            "execute": self._create_tool_executor(tool_name, mcp_tool)
        }

    def _prepare_tool_arguments(self, provided_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize tool invocation arguments for MCP servers."""
        if "arguments" in provided_kwargs:
            raw_arguments = provided_kwargs["arguments"]
            if not isinstance(raw_arguments, dict):
                raise ValueError("Tool arguments must be provided as a dictionary")

            args_payload = raw_arguments.get("args")
            kwargs_payload = raw_arguments.get("kwargs")
            extra_payload = {
                key: value
                for key, value in raw_arguments.items()
                if key not in {"args", "kwargs"}
            }

            if args_payload is None and kwargs_payload is None:
                return {"args": {}, "kwargs": extra_payload}

            merged_kwargs = {**(kwargs_payload or {}), **extra_payload}
            return {"args": args_payload or {}, "kwargs": merged_kwargs}

        args_payload = provided_kwargs.get("args")
        kwargs_payload = provided_kwargs.get("kwargs")
        extra_kwargs = {
            key: value
            for key, value in provided_kwargs.items()
            if key not in {"arguments", "args", "kwargs"}
        }

        if args_payload is None and kwargs_payload is None:
            return {"args": {}, "kwargs": extra_kwargs}

        merged_kwargs = {**(kwargs_payload or {}), **extra_kwargs}
        return {"args": args_payload or {}, "kwargs": merged_kwargs}

    def _create_tool_executor(self, tool_name: str, mcp_tool: Dict[str, Any]):
        """Create an executor function for a tool."""
        async def execute_tool(**kwargs) -> str:
            """Execute the MCP tool through the gateway."""
            try:
                server_name = mcp_tool.get("server") or tool_name.split("_")[0]
                original_tool_name = mcp_tool.get("name")
                if not original_tool_name:
                    parts = tool_name.split("_", 1)
                    original_tool_name = parts[1] if len(parts) > 1 else tool_name

                if not server_name or server_name not in self._connected_servers:
                    return f"Error: Server '{server_name}' not connected"

                connection_info = self._connected_servers[server_name]
                arguments = self._prepare_tool_arguments(kwargs)

                client_handle = connection_info.get("client")
                if client_handle is not None:
                    call_result = await client_handle.call_tool(
                        original_tool_name,
                        arguments,
                    )

                    if getattr(call_result, "isError", False):
                        return str(call_result)

                    parts: List[str] = []
                    for item in getattr(call_result, "content", []) or []:
                        text = getattr(item, "text", None)
                        if text:
                            parts.append(text)

                    if parts:
                        return "\n".join(parts)

                    if hasattr(call_result, "result"):
                        result_value = getattr(call_result, "result")
                        if isinstance(result_value, str):
                            return result_value

                    return str(call_result)

                if not connection_info.get("rest_fallback"):
                    return (
                        f"Error: Protocol client unavailable for server '{server_name}'"
                    )

                logger.debug(
                    f"Using REST fallback execution path for tool '{original_tool_name}' on server '{server_name}'"
                )

                session_id = connection_info.get("session_id")
                if not session_id:
                    return f"Error: Session ID missing for server '{server_name}'"

                if not self._session:
                    return "Error: HTTP session not available for tool execution"

                response = await self._session.post(
                    f"{self.gateway_url}/servers/{server_name}/tools/{original_tool_name}/execute",
                    json={
                        "session_id": session_id,
                        "arguments": arguments,
                    },
                )
                response.raise_for_status()

                result = response.json()
                return result.get("result", "No result returned")

            except Exception as e:
                logger.error(f"Error executing tool '{tool_name}': {e}")
                return f"Error executing {tool_name}: {str(e)}"

        return execute_tool
        
    async def call_tool(self, tool_name: str, **kwargs) -> str:
        """
        Call a specific tool by name.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name not in self._available_tools:
            return f"Error: Tool '{tool_name}' not available"
            
        tool_config = self._available_tools[tool_name]
        executor = self._create_tool_executor(tool_name, tool_config)
        return await executor(**kwargs)


@asynccontextmanager
async def get_mcp_adapter(gateway_url: str = "http://localhost:8811"):
    """
    Context manager for creating and managing an MCP Server Adapter.
    
    Args:
        gateway_url: URL of the Docker MCP Gateway
        
    Yields:
        Configured MCPServerAdapter instance
    """
    adapter = MCPServerAdapter(gateway_url)
    try:
        await adapter.connect()
        yield adapter
    finally:
        await adapter.disconnect()


def create_sync_tool_wrapper(async_tool_func):
    """
    Create a synchronous wrapper for async tool functions.
    
    This is needed because CrewAI agents expect synchronous tool functions.
    """
    def sync_wrapper(**kwargs):
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(async_tool_func(**kwargs))
        
    return sync_wrapper
