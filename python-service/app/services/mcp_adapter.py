"""
MCP Server Adapter for integrating with Docker MCP Gateway.

This module provides the MCPServerAdapter class that connects to the Docker MCP Gateway
and retrieves tools from MCP servers for use with CrewAI agents.
"""
import asyncio
import inspect
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union
from contextlib import asynccontextmanager
from urllib.parse import parse_qs, urlparse

from loguru import logger

import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import Tool as MCPTool


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
            self._session = httpx.AsyncClient(timeout=30.0, follow_redirects=False)
            
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
            
            logger.info(f"MCP Gateway connected. Available servers: {list(servers_data.keys())}")
            
            # Connect to each server and retrieve tools
            for server_name, server_config in servers_data.items():
                await self._connect_to_server(server_name, server_config)
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP Gateway: {e}")
            if self._session:
                await self._session.aclose()
                self._session = None
            raise
            
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

            connect_response = await self._session.post(
                f"{self.gateway_url}/servers/{server_name}/connect",
                follow_redirects=False,
            )

            session_id: Optional[str] = None
            client_handle: Optional[ClientSession] = None
            sse_context = None

            if connect_response.status_code == 307 and "location" in connect_response.headers:
                redirect_location = connect_response.headers["location"]
                if redirect_location.startswith("/"):
                    redirect_url = f"{self.gateway_url}{redirect_location}"
                else:
                    redirect_url = redirect_location

                parsed = urlparse(redirect_url)
                session_id = parse_qs(parsed.query).get("sessionid", [None])[0]
                if not session_id:
                    raise ValueError(
                        f"Missing session identifier in SSE redirect for server '{server_name}'"
                    )

                logger.info(f"Establishing SSE session for {server_name} at {redirect_url}")

                sse_context = sse_client(redirect_url)
                try:
                    read_stream, write_stream = await sse_context.__aenter__()
                    client_handle = ClientSession(read_stream, write_stream)
                    await client_handle.initialize()
                    list_result = await client_handle.list_tools()
                    tools = list(getattr(list_result, "tools", []))
                except Exception as exc:
                    if sse_context is not None:
                        await sse_context.__aexit__(type(exc), exc, exc.__traceback__)
                    raise

                tool_count = self._register_tools(server_name, tools)
                logger.info(
                    f"Connected to SSE server '{server_name}' with {tool_count} tools"
                )

                self._connected_servers[server_name] = {
                    "config": server_config,
                    "session_id": session_id,
                    "client": client_handle,
                    "sse_context": sse_context,
                }
                return

            connect_response.raise_for_status()
            session_id = connect_response.json().get("session_id")

            if not session_id:
                raise ValueError(
                    f"Gateway did not return a session identifier for server '{server_name}'"
                )

            tools_data: Dict[str, Any] = {"tools": []}
            try:
                tools_response = await self._session.get(
                    f"{self.gateway_url}/servers/{server_name}/tools",
                )
                tools_response.raise_for_status()
                tools_data = tools_response.json()
                logger.info(
                    f"Dynamically loaded {len(tools_data.get('tools', []))} tools for {server_name}"
                )
            except Exception as exc:
                logger.warning(f"Could not dynamically load tools for {server_name}: {exc}")

            tool_count = self._register_tools(server_name, tools_data.get("tools", []))
            self._connected_servers[server_name] = {
                "config": server_config,
                "session_id": session_id,
            }

            logger.info(
                f"Connected to MCP server '{server_name}' with {tool_count} tools"
            )

        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{server_name}': {e}")

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
