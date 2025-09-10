"""
MCP Server Adapter for integrating with Docker MCP Gateway.

This module provides the MCPServerAdapter class that connects to the Docker MCP Gateway
and retrieves tools from MCP servers for use with CrewAI agents.
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager
from loguru import logger

import httpx
from mcp import ClientSession
from mcp.types import Tool as MCPTool


class MCPServerAdapter:
    """
    Adapter for connecting to Docker MCP Gateway and managing MCP servers.
    
    This adapter provides context management for MCP connections and tools
    that can be injected into CrewAI agents.
    """
    
    def __init__(self, gateway_url: str = "http://localhost:8080"):
        """
        Initialize the MCP Server Adapter.
        
        Args:
            gateway_url: URL of the Docker MCP Gateway
        """
        self.gateway_url = gateway_url.rstrip('/')
        self._session: Optional[httpx.AsyncClient] = None
        self._connected_servers: Dict[str, Any] = {}
        self._available_tools: Dict[str, MCPTool] = {}
        
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
            self._session = httpx.AsyncClient(timeout=30.0)
            
            # Check gateway health
            response = await self._session.get(f"{self.gateway_url}/health")
            response.raise_for_status()
            
            # Get available servers
            servers_response = await self._session.get(f"{self.gateway_url}/servers")
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
            # Request server connection through gateway
            connect_response = await self._session.post(
                f"{self.gateway_url}/servers/{server_name}/connect"
            )
            connect_response.raise_for_status()
            
            # Get server tools
            tools_response = await self._session.get(
                f"{self.gateway_url}/servers/{server_name}/tools"
            )
            tools_response.raise_for_status()
            tools_data = tools_response.json()
            
            # Store server connection and tools
            self._connected_servers[server_name] = {
                "config": server_config,
                "session_id": connect_response.json().get("session_id")
            }
            
            # Register tools from this server
            for tool_data in tools_data.get("tools", []):
                tool_name = f"{server_name}_{tool_data['name']}"
                self._available_tools[tool_name] = tool_data
                
            logger.info(f"Connected to MCP server '{server_name}' with {len(tools_data.get('tools', []))} tools")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{server_name}': {e}")
            
    async def _disconnect_from_server(self, server_name: str) -> None:
        """Disconnect from a specific MCP server."""
        if server_name in self._connected_servers:
            try:
                session_id = self._connected_servers[server_name].get("session_id")
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
                server_name = tool_name.split("_")[0]
                original_tool_name = "_".join(tool_name.split("_")[1:])
                
                if server_name not in self._connected_servers:
                    return f"Error: Server '{server_name}' not connected"
                    
                session_id = self._connected_servers[server_name]["session_id"]
                
                # Execute tool through gateway
                response = await self._session.post(
                    f"{self.gateway_url}/servers/{server_name}/tools/{original_tool_name}/execute",
                    json={
                        "session_id": session_id,
                        "arguments": kwargs
                    }
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
async def get_mcp_adapter(gateway_url: str = "http://localhost:8080"):
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