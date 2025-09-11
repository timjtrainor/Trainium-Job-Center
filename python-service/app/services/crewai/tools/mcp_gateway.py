"""
MCP Gateway Tool for CrewAI

This module provides a CrewAI tool that integrates with the MCP Gateway service,
allowing CrewAI agents to interact with Model Context Protocol (MCP) servers.

The tool follows MCP standards and provides a clean interface for agents to:
- Search the web via DuckDuckGo
- Execute commands through various MCP servers
- Extend functionality by adding new MCP servers to the gateway
"""

from typing import Any, Dict, List, Optional, Type
import httpx
import json
from loguru import logger
from pydantic import BaseModel, Field

from crewai_tools import BaseTool


class MCPSearchInput(BaseModel):
    """Input schema for MCP search operations"""
    query: str = Field(description="Search query to execute")
    server: str = Field(default="duckduckgo", description="MCP server to use for search (default: duckduckgo)")
    max_results: Optional[int] = Field(default=5, description="Maximum number of results to return")


class MCPGatewayTool(BaseTool):
    """
    CrewAI tool for interacting with MCP Gateway services.
    
    This tool allows CrewAI agents to:
    - Perform web searches via DuckDuckGo MCP server
    - Execute commands on other MCP servers available through the gateway
    - Get information about available MCP servers
    
    The tool is designed to be extensible - new MCP servers can be added to the
    gateway configuration without changing this tool's code.
    """
    
    name: str = "mcp_gateway"
    description: str = (
        "Access Model Context Protocol (MCP) services through the MCP Gateway. "
        "Use this tool to search the web, access external APIs, and interact with "
        "various services that implement the MCP standard. The tool currently "
        "supports DuckDuckGo web search and can be extended with additional MCP servers."
    )
    args_schema: Type[BaseModel] = MCPSearchInput
    
    def __init__(self, gateway_url: str = "http://localhost:3000", **kwargs):
        """
        Initialize the MCP Gateway tool.
        
        Args:
            gateway_url: URL of the MCP Gateway service
            **kwargs: Additional keyword arguments for BaseTool
        """
        super().__init__(**kwargs)
        self.gateway_url = gateway_url.rstrip('/')
        self._client = httpx.Client()
        
    def _execute(self, query: str, server: str = "duckduckgo", max_results: int = 5) -> str:
        """
        Execute a search query through the MCP Gateway.
        
        Args:
            query: The search query to execute
            server: MCP server to use (default: duckduckgo)
            max_results: Maximum number of results to return
            
        Returns:
            Formatted search results as a string
        """
        try:
            # First, check if the gateway is available
            health_response = self._client.get(f"{self.gateway_url}/health")
            if health_response.status_code != 200:
                return f"MCP Gateway is not available. Health check failed with status {health_response.status_code}"
            
            # Prepare the MCP call
            mcp_request = {
                "server": server,
                "method": "search",
                "params": {
                    "query": query,
                    "max_results": max_results
                }
            }
            
            # Call the MCP Gateway
            response = self._client.post(
                f"{self.gateway_url}/call",
                json=mcp_request,
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_detail = response.text if response.text else "Unknown error"
                return f"MCP Gateway call failed with status {response.status_code}: {error_detail}"
            
            result_data = response.json()
            
            if not result_data.get("success", False):
                error_msg = result_data.get("error", "Unknown error")
                return f"MCP server call failed: {error_msg}"
            
            # Parse the search results
            mcp_result = result_data.get("result", {})
            
            # Handle JSON-RPC response structure
            if "result" in mcp_result:
                search_results = mcp_result["result"]
            else:
                search_results = mcp_result
            
            # Format the results for the agent
            return self._format_search_results(search_results, query)
            
        except httpx.TimeoutException:
            return f"MCP Gateway request timed out. The search query '{query}' could not be completed."
        except httpx.RequestError as e:
            return f"Network error connecting to MCP Gateway: {str(e)}"
        except json.JSONDecodeError:
            return "Invalid response format from MCP Gateway"
        except Exception as e:
            logger.error(f"Unexpected error in MCP Gateway tool: {e}")
            return f"Unexpected error occurred: {str(e)}"
    
    def _format_search_results(self, results: Any, query: str) -> str:
        """
        Format search results for display to the agent.
        
        Args:
            results: Raw search results from MCP server
            query: Original search query
            
        Returns:
            Formatted results string
        """
        if not results:
            return f"No results found for query: '{query}'"
        
        # Handle different result formats
        if isinstance(results, list):
            formatted_results = []
            for i, result in enumerate(results[:5], 1):  # Limit to 5 results
                if isinstance(result, dict):
                    title = result.get("title", "No title")
                    url = result.get("url", "No URL")
                    snippet = result.get("snippet", result.get("description", "No description"))
                    
                    formatted_results.append(f"{i}. **{title}**\n   URL: {url}\n   Summary: {snippet}\n")
                else:
                    formatted_results.append(f"{i}. {str(result)}\n")
            
            return f"Search results for '{query}':\n\n" + "\n".join(formatted_results)
        
        elif isinstance(results, dict):
            if "items" in results:
                return self._format_search_results(results["items"], query)
            else:
                return f"Search completed for '{query}'. Results: {json.dumps(results, indent=2)}"
        
        else:
            return f"Search results for '{query}': {str(results)}"
    
    def get_available_servers(self) -> List[str]:
        """
        Get list of available MCP servers from the gateway.
        
        Returns:
            List of available server names
        """
        try:
            response = self._client.get(f"{self.gateway_url}/servers")
            if response.status_code == 200:
                data = response.json()
                return list(data.get("servers", {}).keys())
            else:
                logger.warning(f"Failed to get server list: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting server list: {e}")
            return []
    
    def __del__(self):
        """Clean up the HTTP client on destruction"""
        if hasattr(self, '_client'):
            self._client.close()


# Tool factory function
def create_mcp_gateway_tool(gateway_url: str = "http://mcp-gateway:3000") -> MCPGatewayTool:
    """
    Factory function to create an MCP Gateway tool instance.
    
    Args:
        gateway_url: URL of the MCP Gateway service (default: http://mcp-gateway:3000 for Docker)
        
    Returns:
        Configured MCPGatewayTool instance
    """
    return MCPGatewayTool(gateway_url=gateway_url)


# For backwards compatibility and easy imports
mcp_gateway_tool = create_mcp_gateway_tool()