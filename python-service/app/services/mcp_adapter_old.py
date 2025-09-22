"""
MCP Server Adapter for Docker MCP Gateway using MCP Toolkit with stdio transport.

This module provides the MCPServerAdapter class that uses the official MCP Toolkit
with ClientSession and stdio transport to connect to the Docker MCP Gateway.
This replaces the previous HTTP REST API approach with the proper MCP protocol.
"""
import asyncio
import subprocess
from typing import Dict, List, Any, Optional, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

try:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from mcp.types import Tool as MCPTool
except ImportError:
    logger.error("MCP package not available. Install with: pip install mcp")
    # Create mock classes for backward compatibility
    class ClientSession:
        async def initialize(self): return {}
        async def list_tools(self): return type('Tools', (), {'tools': []})()
        async def call_tool(self, name, args): return {"result": f"Mock result for {name}"}
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
    
    class StdioServerParameters:
        def __init__(self, command, args, env): pass
    
    def stdio_client(params):
        return ClientSession()
        
    class MCPTool:
        def __init__(self, name, description, inputSchema=None):
            self.name = name
            self.description = description  
            self.inputSchema = inputSchema


@dataclass
class AdapterConfig:
    """Configuration for MCP Server Adapter using MCP Toolkit."""
    gateway_command: List[str] = None
    gateway_args: Optional[Dict[str, str]] = None
    connection_timeout: int = 30
    discovery_timeout: int = 60
    execution_timeout: int = 120
    
    def __post_init__(self):
        if self.gateway_command is None:
            # Default command to connect to Docker MCP Gateway via stdio
            self.gateway_command = [
                "docker", "exec", "-i", "trainium_mcp_gateway", 
                "mcp-gateway", "--transport=stdio"
            ]


class MCPServerAdapter:
    """
    Adapter for connecting to Docker MCP Gateway with stdio transport.
    
    This adapter connects to the Docker MCP Gateway via HTTP REST API.
    The gateway uses stdio transport internally to communicate with MCP servers,
    providing better reliability than SSE transport.
    
    Features:
    - HTTP REST API communication with gateway
    - Automatic server discovery from gateway
    - Comprehensive logging for debugging
    - Configurable timeouts and resilience
    - Tool discovery and execution through gateway
    """
    
    def __init__(self, config: Optional[AdapterConfig] = None):
        """
        Initialize the MCP Server Adapter.
        
        Args:
            config: Adapter configuration (uses defaults if None)
        """
        self.config = config or AdapterConfig()
        self._session: Optional[httpx.AsyncClient] = None
        self._available_servers: Dict[str, Any] = {}
        self._available_tools: Dict[str, Dict[str, Any]] = {}
        self._server_sessions: Dict[str, str] = {}  # server_name -> session_id
        self._connected = False
        
        logger.info(f"MCP Adapter initialized for gateway: {self.config.gateway_url}")
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self) -> None:
        """Connect to the MCP Gateway and discover available servers."""
        try:
            # Create HTTP client for gateway communication
            self._session = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.config.connection_timeout,
                    read=self.config.discovery_timeout,
                    write=self.config.execution_timeout,
                    pool=self.config.connection_timeout
                ),
                verify=self.config.verify_tls
            )
            
            logger.info("Connecting to MCP Gateway...")
            
            # Check gateway health
            await self._check_gateway_health()
            
            # Discover available servers from gateway
            await self._discover_servers()
            
            # Connect to each server through the gateway
            await self._connect_to_servers()
            
            # Discover all available tools
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
            logger.info("Checking MCP Gateway health...")
            response = await self._session.get(f"{self.config.gateway_url}/health")
            response.raise_for_status()
            health_data = response.json()
            logger.info(f"Gateway health check passed: {health_data}")
        except Exception as e:
            raise ConnectionError(f"Gateway health check failed: {e}")
            
    async def _discover_servers(self) -> None:
        """Discover available servers from the gateway."""
        try:
            logger.info("Discovering available servers from gateway...")
            response = await self._session.get(f"{self.config.gateway_url}/servers")
            response.raise_for_status()
            
            servers_data = response.json()
            self._available_servers = servers_data
            logger.info(f"Discovered {len(servers_data)} servers: {list(servers_data.keys())}")
            
        except Exception as e:
            logger.error(f"Server discovery failed: {e}")
            # Use default servers if discovery fails
            self._available_servers = {
                "duckduckgo": {"description": "DuckDuckGo search server"},
                "linkedin-mcp-server": {"description": "LinkedIn MCP server"}
            }
            logger.warning(f"Using default servers: {list(self._available_servers.keys())}")
            
    async def _connect_to_servers(self) -> None:
        """Connect to each discovered server through the gateway."""
        logger.info("Connecting to servers through gateway...")
        
        for server_name in self._available_servers.keys():
            try:
                logger.info(f"Connecting to server: {server_name}")
                await self._connect_to_server(server_name)
                logger.info(f"Successfully connected to {server_name}")
                
            except Exception as e:
                logger.error(f"Failed to connect to {server_name}: {e}")
                # Continue with other servers
                continue
                
    async def _connect_to_server(self, server_name: str) -> None:
        """Connect to a specific server through the gateway."""
        try:
            response = await self._session.post(
                f"{self.config.gateway_url}/servers/{server_name}/connect"
            )
            response.raise_for_status()
            
            connection_data = response.json()
            session_id = connection_data.get("session_id")
            
            if session_id:
                self._server_sessions[server_name] = session_id
                logger.info(f"Connected to {server_name} with session: {session_id}")
            else:
                logger.warning(f"No session ID returned for {server_name}")
                
        except Exception as e:
            logger.error(f"Error connecting to server {server_name}: {e}")
            raise
            
    async def _discover_all_tools(self) -> None:
        """Discover all tools from connected servers."""
        logger.info("Discovering tools from all connected servers...")
        
        for server_name in self._server_sessions.keys():
            try:
                await self._discover_server_tools(server_name)
            except Exception as e:
                logger.warning(f"Failed to discover tools for {server_name}: {e}")
                # Continue with other servers
                continue
                
    async def _discover_server_tools(self, server_name: str) -> None:
        """Discover tools from a specific server."""
        try:
            logger.info(f"Discovering tools for {server_name}")
            
            response = await self._session.get(
                f"{self.config.gateway_url}/servers/{server_name}/tools"
            )
            response.raise_for_status()
            
            tools_data = response.json()
            tools = tools_data.get("tools", [])
            
            logger.info(f"Found {len(tools)} tools for {server_name}")
            
            # Register each tool with server prefix
            for tool_data in tools:
                tool_name = f"{server_name}_{tool_data['name']}"
                
                self._available_tools[tool_name] = {
                    **tool_data,
                    "server": server_name,
                    "original_name": tool_data["name"]
                }
                
                logger.info(f"Registered tool: {tool_name} - {tool_data.get('description', 'No description')}")
                
        except Exception as e:
            logger.error(f"Failed to discover tools for {server_name}: {e}")
            
    async def disconnect(self) -> None:
        """Disconnect from the MCP Gateway and clean up resources."""
        logger.info("Disconnecting from MCP Gateway...")
        
        # Disconnect from all servers
        for server_name, session_id in self._server_sessions.items():
            try:
                await self._disconnect_from_server(server_name, session_id)
            except Exception as e:
                logger.warning(f"Error disconnecting from {server_name}: {e}")
                
        await self._cleanup()
        self._connected = False
        logger.info("MCP Gateway disconnected successfully")
        
    async def _disconnect_from_server(self, server_name: str, session_id: str) -> None:
        """Disconnect from a specific server."""
        try:
            logger.info(f"Disconnecting from {server_name}")
            
            response = await self._session.post(
                f"{self.config.gateway_url}/servers/{server_name}/disconnect",
                json={"session_id": session_id}
            )
            response.raise_for_status()
            
            logger.info(f"Successfully disconnected from {server_name}")
            
        except Exception as e:
            logger.warning(f"Error disconnecting from {server_name}: {e}")
            
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
        self._available_servers.clear()
        self._available_tools.clear()
        self._server_sessions.clear()
        
    def list_servers(self) -> List[str]:
        """
        List available MCP servers.
        
        Returns:
            List of connected server names
        """
        return list(self._server_sessions.keys())
        
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
        Execute a tool on the specified server through the gateway.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if not self._connected:
            raise RuntimeError("Adapter not connected to gateway")
            
        if server_name not in self._server_sessions:
            raise ValueError(f"Server '{server_name}' not connected")
            
        # Find the tool
        full_tool_name = f"{server_name}_{tool_name}"
        if full_tool_name not in self._available_tools:
            raise ValueError(f"Tool '{tool_name}' not found on server '{server_name}'")
            
        session_id = self._server_sessions[server_name]
        
        try:
            logger.info(f"Executing tool {tool_name} on {server_name} with args: {arguments}")
            
            response = await self._session.post(
                f"{self.config.gateway_url}/servers/{server_name}/tools/{tool_name}/execute",
                json={
                    "session_id": session_id,
                    "arguments": arguments,
                },
                timeout=httpx.Timeout(read=self.config.execution_timeout)
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Tool {tool_name} executed successfully on {server_name}")
            logger.debug(f"Tool result: {str(result.get('result', ''))[:200]}...")
            
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
            "discovered_servers": list(self._available_servers.keys()),
            "connected_servers": list(self._server_sessions.keys()),
            "server_sessions": dict(self._server_sessions),
            "tools_count": len(self._available_tools),
            "tools": list(self._available_tools.keys()),
            "config": {
                "connection_timeout": self.config.connection_timeout,
                "discovery_timeout": self.config.discovery_timeout,
                "execution_timeout": self.config.execution_timeout,
                "verify_tls": self.config.verify_tls,
                "max_retries": self.config.max_retries,
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