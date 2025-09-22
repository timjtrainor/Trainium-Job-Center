"""
Proper Docker MCP Gateway Connection Implementation.

This module provides the MCPServerAdapter class that implements robust connection
to the Docker MCP Gateway following its design specifications for discovery,
transport, security, and tool execution.
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager
from urllib.parse import parse_qs, urlparse
from dataclasses import dataclass

from loguru import logger

import httpx
from mcp import ClientSession
from mcp.types import Tool as MCPTool


@dataclass
class AdapterConfig:
    """Configuration for MCP Server Adapter."""
    gateway_url: str = "http://localhost:8811"
    connection_timeout: int = 30
    discovery_timeout: int = 60
    execution_timeout: int = 120
    verify_tls: bool = True
    max_retries: int = 3


class MCPServerAdapter:
    """
    Robust adapter for connecting to Docker MCP Gateway.
    
    This adapter implements the Docker MCP Gateway connection specification with:
    - Gateway discovery with 307 redirect handling
    - Unified SSE transport for all servers
    - Configurable timeouts and resilience
    - Secure credentials handling
    - Comprehensive error handling and diagnostics
    """
    
    def __init__(self, config: Optional[AdapterConfig] = None):
        """
        Initialize the MCP Server Adapter.
        
        Args:
            config: Adapter configuration (uses defaults if None)
        """
        self.config = config or AdapterConfig()
        self._session: Optional[httpx.AsyncClient] = None
        self._sse_endpoint: Optional[str] = None
        self._session_id: Optional[str] = None
        self._available_servers: Dict[str, Any] = {}
        self._available_tools: Dict[str, Dict[str, Any]] = {}
        self._connected = False
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self) -> None:
        """Connect to the MCP Gateway and initialize servers following the specification."""
        try:
            # Step 1: Create HTTP client with proper configuration
            self._session = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.config.connection_timeout,
                    read=self.config.discovery_timeout,
                    write=self.config.execution_timeout,
                    pool=self.config.connection_timeout
                ),
                follow_redirects=False,  # Handle redirects manually per spec
                verify=self.config.verify_tls
            )
            
            # Step 2: Health check
            await self._check_gateway_health()
            
            # Step 3: Gateway discovery - GET /servers without auto-redirect
            await self._discover_gateway_endpoint()
            
            # Step 4: Initialize transport and session
            await self._initialize_transport()
            
            # Step 5: Discover all available tools through unified session
            await self._discover_all_tools()
            
            self._connected = True
            logger.info(
                f"MCP Gateway connected successfully. "
                f"Servers: {list(self._available_servers.keys())}, "
                f"Tools: {len(self._available_tools)}"
            )
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP Gateway: {e}")
            await self._cleanup()
            raise
            
    async def _check_gateway_health(self) -> None:
        """Check gateway health before attempting connection."""
        try:
            response = await self._session.get(f"{self.config.gateway_url}/health")
            response.raise_for_status()
            health_data = response.json()
            logger.info(f"Gateway health check passed: {health_data}")
        except Exception as e:
            raise ConnectionError(f"Gateway health check failed: {e}")
            
    async def _discover_gateway_endpoint(self) -> None:
        """
        Discover gateway endpoint following the specification.
        
        Send GET {gateway_url}/servers without auto-redirect.
        Handle 307 Temporary Redirect to extract SSE endpoint and session.
        """
        logger.info("Discovering gateway endpoint...")
        
        try:
            response = await self._session.get(f"{self.config.gateway_url}/servers")
            
            if response.status_code == 307:
                # Extract Location header for SSE endpoint
                location = response.headers.get("location")
                if not location:
                    raise ValueError("307 redirect missing Location header")
                    
                # Handle relative URLs
                if location.startswith("/"):
                    self._sse_endpoint = f"{self.config.gateway_url}{location}"
                else:
                    self._sse_endpoint = location
                    
                # Extract session ID from URL if present
                parsed_url = urlparse(self._sse_endpoint)
                query_params = parse_qs(parsed_url.query)
                self._session_id = query_params.get("sessionid", [None])[0]
                
                logger.info(f"Gateway using SSE transport: {self._sse_endpoint}")
                if self._session_id:
                    logger.info(f"Session ID extracted: {self._session_id}")
                    
            elif response.status_code == 200:
                # Parse JSON response for server list
                servers_data = response.json()
                self._available_servers = servers_data
                logger.info(f"Gateway returned server list: {list(servers_data.keys())}")
                
            else:
                response.raise_for_status()
                
        except Exception as e:
            raise ConnectionError(f"Gateway discovery failed: {e}")
            
    async def _initialize_transport(self) -> None:
        """Initialize transport connection (SSE or direct)."""
        if self._sse_endpoint:
            logger.info("Initializing SSE transport...")
            try:
                # Establish SSE connection
                sse_response = await self._session.get(
                    self._sse_endpoint,
                    headers={"Accept": "text/event-stream"},
                    timeout=httpx.Timeout(
                        connect=self.config.connection_timeout,
                        read=self.config.discovery_timeout,
                        write=self.config.execution_timeout,
                        pool=self.config.connection_timeout
                    )
                )
                sse_response.raise_for_status()
                
                logger.info("SSE transport initialized successfully")
                
                # For SSE transport, we need to get server list from gateway
                await self._get_enabled_servers()
                
            except Exception as e:
                raise ConnectionError(f"SSE transport initialization failed: {e}")
        else:
            logger.info("Using direct HTTP transport")
            
    async def _get_enabled_servers(self) -> None:
        """Get list of enabled servers from gateway configuration."""
        if not self._available_servers:
            # Default servers for SSE transport - these should be configured in gateway
            # This matches the docker-compose configuration
            self._available_servers = {
                "duckduckgo": {"transport": "sse", "endpoint": self._sse_endpoint},
                "linkedin-mcp-server": {"transport": "sse", "endpoint": self._sse_endpoint}
            }
            logger.info(f"Using default server configuration: {list(self._available_servers.keys())}")
            
    async def _discover_all_tools(self) -> None:
        """Discover all tools available via the gateway through unified session."""
        logger.info("Discovering available tools...")
        
        for server_name in self._available_servers.keys():
            try:
                await self._discover_server_tools(server_name)
            except Exception as e:
                logger.warning(f"Failed to discover tools for {server_name}: {e}")
                # Continue with other servers - per spec, fallback gracefully
                
    async def _discover_server_tools(self, server_name: str) -> None:
        """Discover tools for a specific server."""
        try:
            # Try to get tools from gateway endpoint
            tools_response = await self._session.get(
                f"{self.config.gateway_url}/servers/{server_name}/tools",
                timeout=httpx.Timeout(
                    connect=self.config.connection_timeout,
                    read=self.config.discovery_timeout,
                    write=self.config.execution_timeout,
                    pool=self.config.connection_timeout
                )
            )
            
            if tools_response.status_code == 404:
                logger.info(f"Server {server_name} not connected or has no tools")
                return
                
            tools_response.raise_for_status()
            tools_data = tools_response.json()
            
            # Register tools with server namespace
            for tool_data in tools_data.get("tools", []):
                tool_name = f"{server_name}_{tool_data['name']}"
                self._available_tools[tool_name] = {
                    **tool_data,
                    "server": server_name,
                    "original_name": tool_data["name"]
                }
                
            logger.info(f"Discovered {len(tools_data.get('tools', []))} tools for {server_name}")
            
        except httpx.TimeoutException:
            logger.warning(f"Tool discovery timeout for {server_name}")
        except Exception as e:
            logger.warning(f"Tool discovery failed for {server_name}: {e}")
            
    async def disconnect(self) -> None:
        """Disconnect from the MCP Gateway and clean up resources."""
        logger.info("Disconnecting from MCP Gateway...")
        await self._cleanup()
        self._connected = False
        logger.info("MCP Gateway disconnected successfully")
        
    async def _cleanup(self) -> None:
        """Clean up resources and connections."""
        if self._session:
            try:
                await self._session.aclose()
            except Exception as e:
                logger.warning(f"Error during session cleanup: {e}")
            finally:
                self._session = None
                
        # Reset state
        self._sse_endpoint = None
        self._session_id = None
        self._available_servers.clear()
        self._available_tools.clear()
        
    def list_servers(self) -> List[str]:
        """
        List available MCP servers.
        
        Returns:
            List of server names
        """
        return list(self._available_servers.keys())
        
    def list_tools(self, server_name: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        List available tools, optionally filtered by server.
        
        Args:
            server_name: Optional server name to filter tools
            
        Returns:
            Dictionary of tool name to tool configuration
        """
        if server_name:
            return {
                name: config for name, config in self._available_tools.items()
                if config.get("server") == server_name
            }
        return dict(self._available_tools)
        
    def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available tools from connected MCP servers.
        
        Returns:
            Dictionary of tool name to tool configuration
        """
        return dict(self._available_tools)
        
    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool on the specified server through shared transport.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if not self._connected:
            raise RuntimeError("Adapter not connected to gateway")
            
        if server_name not in self._available_servers:
            raise ValueError(f"Server '{server_name}' not available")
            
        # Find the tool
        full_tool_name = f"{server_name}_{tool_name}"
        if full_tool_name not in self._available_tools:
            raise ValueError(f"Tool '{tool_name}' not found on server '{server_name}'")
            
        try:
            # Execute through gateway API
            response = await self._session.post(
                f"{self.config.gateway_url}/servers/{server_name}/tools/{tool_name}/execute",
                json={
                    "session_id": self._session_id,
                    "arguments": arguments,
                },
                timeout=httpx.Timeout(
                    connect=self.config.connection_timeout,
                    read=self.config.execution_timeout,
                    write=self.config.execution_timeout,
                    pool=self.config.connection_timeout
                )
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Tool '{tool_name}' executed successfully on server '{server_name}'")
            return result
            
        except httpx.TimeoutException:
            logger.error(f"Tool execution timeout: {server_name}.{tool_name}")
            raise TimeoutError(f"Tool execution timeout: {server_name}.{tool_name}")
        except Exception as e:
            logger.error(f"Tool execution failed: {server_name}.{tool_name}: {e}")
            raise
            
    def get_diagnostics(self) -> Dict[str, Any]:
        """Provide diagnostic information for troubleshooting."""
        return {
            "connected": self._connected,
            "gateway_url": self.config.gateway_url,
            "sse_endpoint": self._sse_endpoint,
            "session_id": self._session_id,
            "servers": list(self._available_servers.keys()),
            "tools_count": len(self._available_tools),
            "tools": list(self._available_tools.keys()),
            "config": {
                "connection_timeout": self.config.connection_timeout,
                "discovery_timeout": self.config.discovery_timeout,
                "execution_timeout": self.config.execution_timeout,
                "verify_tls": self.config.verify_tls,
            }
        }
    # Legacy compatibility methods for existing code
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all available tools from connected MCP servers.
        
        Returns:
            Dictionary of tool name to tool configuration
        """
        return self.get_all_tools()
        
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
        
    def _create_tool_executor(self, tool_name: str, mcp_tool: Dict[str, Any]):
        """Create an executor function for a tool."""
        async def execute_tool(**kwargs) -> str:
            """Execute the MCP tool through the gateway."""
            try:
                server_name = mcp_tool.get("server")
                original_tool_name = mcp_tool.get("original_name")
                
                if not server_name or not original_tool_name:
                    return f"Error: Tool configuration incomplete for '{tool_name}'"
                
                result = await self.execute_tool(server_name, original_tool_name, kwargs)
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
        server_name = tool_config.get("server")
        original_name = tool_config.get("original_name")
        
        if not server_name or not original_name:
            return f"Error: Tool configuration incomplete for '{tool_name}'"
            
        try:
            result = await self.execute_tool(server_name, original_name, kwargs)
            return result.get("result", "No result returned")
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"


@asynccontextmanager
async def get_mcp_adapter(gateway_url: str = "http://localhost:8811", config: Optional[AdapterConfig] = None):
    """
    Context manager for creating and managing an MCP Server Adapter.
    
    Args:
        gateway_url: URL of the Docker MCP Gateway (legacy parameter for compatibility)
        config: Adapter configuration (overrides gateway_url if provided)
        
    Yields:
        Configured MCPServerAdapter instance
    """
    if config is None:
        config = AdapterConfig(gateway_url=gateway_url)
    elif gateway_url != "http://localhost:8811":
        # Override config gateway_url if explicitly provided
        config.gateway_url = gateway_url
        
    adapter = MCPServerAdapter(config)
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