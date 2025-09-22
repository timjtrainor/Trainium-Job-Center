"""
MCP Toolkit-based adapter for Docker MCP Gateway using stdio transport.

This module uses the official MCP Toolkit with ClientSession and stdio transport
to connect to the Docker MCP Gateway, discover servers and tools, and provide
CrewAI-compatible tool functions.
"""
import asyncio
import subprocess
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from contextlib import asynccontextmanager

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

try:
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
except ImportError:
    logger.error("MCP package not available. Install with: pip install mcp")
    # Create mock classes for testing
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


@dataclass
class MCPToolkitConfig:
    """Configuration for MCP Toolkit adapter."""
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


class MCPToolkitAdapter:
    """
    MCP Toolkit-based adapter using ClientSession and stdio transport.
    
    This adapter uses the official MCP Toolkit to connect to the Docker MCP Gateway
    via stdio transport, discovers all available servers and tools, and provides
    CrewAI-compatible sync tool functions.
    """
    
    def __init__(self, config: Optional[MCPToolkitConfig] = None):
        """Initialize the MCP Toolkit adapter."""
        self.config = config or MCPToolkitConfig()
        self.session: Optional[ClientSession] = None
        self._available_servers: List[str] = []
        self._available_tools: Dict[str, Dict[str, Any]] = {}
        self._connected = False
        
        logger.info("MCP Toolkit Adapter initialized")
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self) -> None:
        """Connect to the Docker MCP Gateway using stdio transport."""
        try:
            logger.info("Connecting to Docker MCP Gateway via stdio transport...")
            
            # Create stdio server parameters for the gateway connection
            server_params = StdioServerParameters(
                command=self.config.gateway_command[0],
                args=self.config.gateway_command[1:],
                env=self.config.gateway_args or {}
            )
            
            # Create stdio client and session
            stdio_client_instance = stdio_client(server_params)
            
            # Initialize the session
            self.session = await stdio_client_instance.__aenter__()
            
            logger.info("Connected to MCP Gateway via stdio transport")
            
            # Initialize the session
            init_result = await self.session.initialize()
            logger.info(f"Session initialized: {init_result}")
            
            # Discover available servers and tools
            await self._discover_servers_and_tools()
            
            self._connected = True
            logger.info(
                f"MCP Gateway connection complete. "
                f"Servers: {len(self._available_servers)}, "
                f"Tools: {len(self._available_tools)}"
            )
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP Gateway: {e}")
            await self.disconnect()
            raise
            
    async def _discover_servers_and_tools(self) -> None:
        """Discover all available servers and their tools."""
        try:
            logger.info("Discovering servers and tools...")
            
            # List all available tools (this includes tools from all servers)
            tools_result = await self.session.list_tools()
            logger.info(f"Discovered {len(tools_result.tools)} tools")
            
            # Process each tool and organize by server
            for tool in tools_result.tools:
                tool_name = tool.name
                
                # Determine server name from tool name (convention: server_toolname)
                server_name = "unknown"
                if "_" in tool_name:
                    potential_server = tool_name.split("_")[0]
                    if potential_server in ["duckduckgo", "linkedin"]:
                        server_name = potential_server
                        
                # Add server to available servers list
                if server_name not in self._available_servers:
                    self._available_servers.append(server_name)
                    logger.info(f"Discovered server: {server_name}")
                
                # Store tool information
                self._available_tools[tool_name] = {
                    "name": tool_name,
                    "description": tool.description or f"Tool from {server_name} server",
                    "parameters": tool.inputSchema.model_dump() if tool.inputSchema else {},
                    "server": server_name,
                    "mcp_tool": tool
                }
                
            logger.info(f"Discovery complete: {len(self._available_servers)} servers, {len(self._available_tools)} tools")
            
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}")
            # Set defaults if discovery fails
            self._available_servers = ["duckduckgo", "linkedin"]
            self._available_tools = {}
            
    async def disconnect(self) -> None:
        """Disconnect from the MCP Gateway."""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
                logger.info("Disconnected from MCP Gateway")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.session = None
                self._connected = False
                
    def get_available_servers(self) -> List[str]:
        """Get list of available MCP servers."""
        return self._available_servers.copy()
        
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get all available tools from all servers."""
        return self._available_tools.copy()
        
    def get_tools_for_server(self, server_name: str) -> Dict[str, Dict[str, Any]]:
        """Get tools for a specific server."""
        return {
            name: config for name, config in self._available_tools.items()
            if config.get("server") == server_name
        }
        
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with the given arguments."""
        if not self._connected or not self.session:
            raise RuntimeError("Not connected to MCP Gateway")
            
        if tool_name not in self._available_tools:
            raise ValueError(f"Tool '{tool_name}' not found")
            
        try:
            logger.info(f"Executing tool: {tool_name} with args: {arguments}")
            
            # Call the tool using the MCP session
            result = await self.session.call_tool(tool_name, arguments)
            
            logger.info(f"Tool execution completed: {tool_name}")
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            raise
            
    def get_crewai_tools(self) -> List[Dict[str, Any]]:
        """
        Get all discovered tools formatted for CrewAI compatibility.
        
        Returns a list of tool dictionaries with:
        - name: Tool name
        - description: Tool description  
        - parameters: Tool parameters schema
        - execute: Synchronous execution function
        """
        crewai_tools = []
        
        for tool_name, tool_config in self._available_tools.items():
            # Create a synchronous wrapper for the async execute function
            def create_sync_executor(name: str):
                def sync_execute(**kwargs) -> Any:
                    """Synchronous tool executor for CrewAI."""
                    try:
                        # Run the async execute_tool in a new event loop if needed
                        loop = None
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # If loop is running, we need to use asyncio.create_task
                                # But CrewAI expects sync functions, so we'll use run_in_executor
                                import concurrent.futures
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(asyncio.run, self.execute_tool(name, kwargs))
                                    return future.result()
                            else:
                                return loop.run_until_complete(self.execute_tool(name, kwargs))
                        except RuntimeError:
                            # No event loop exists, create a new one
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                return loop.run_until_complete(self.execute_tool(name, kwargs))
                            finally:
                                loop.close()
                                
                    except Exception as e:
                        logger.error(f"Sync tool execution failed for {name}: {e}")
                        return f"Error: {str(e)}"
                        
                return sync_execute
                
            crewai_tool = {
                "name": tool_name,
                "description": tool_config["description"],
                "parameters": tool_config.get("parameters", {}),
                "execute": create_sync_executor(tool_name)
            }
            
            crewai_tools.append(crewai_tool)
            
        logger.info(f"Prepared {len(crewai_tools)} tools for CrewAI")
        return crewai_tools


@asynccontextmanager  
async def get_mcp_toolkit_adapter(config: Optional[MCPToolkitConfig] = None):
    """
    Context manager for creating and managing an MCP Toolkit Adapter.
    
    Args:
        config: MCP Toolkit configuration
        
    Yields:
        Configured MCPToolkitAdapter instance
    """
    adapter = MCPToolkitAdapter(config)
    try:
        await adapter.connect()
        yield adapter
    finally:
        await adapter.disconnect()


# Demonstration function
async def demo_mcp_toolkit():
    """Demonstrate the MCP Toolkit adapter functionality."""
    try:
        logger.info("=== MCP Toolkit Adapter Demo ===")
        
        # Create and connect to the adapter
        async with get_mcp_toolkit_adapter() as adapter:
            
            # Show available servers
            servers = adapter.get_available_servers()
            logger.info(f"Available servers: {servers}")
            
            # Show available tools
            tools = adapter.get_available_tools()
            logger.info(f"Available tools: {list(tools.keys())}")
            
            # Get CrewAI-compatible tools
            crewai_tools = adapter.get_crewai_tools()
            logger.info(f"CrewAI tools prepared: {len(crewai_tools)}")
            
            # Demonstrate tool execution (if any tools are available)
            if crewai_tools:
                first_tool = crewai_tools[0]
                logger.info(f"Testing tool: {first_tool['name']}")
                
                # Example execution - adjust parameters based on actual tool
                if "search" in first_tool['name'].lower():
                    result = first_tool['execute'](query="test search")
                    logger.info(f"Tool result: {result}")
                else:
                    logger.info(f"Tool {first_tool['name']} requires specific parameters")
                    
        logger.info("=== Demo Complete ===")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demo_mcp_toolkit())