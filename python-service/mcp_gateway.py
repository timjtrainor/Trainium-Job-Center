"""
Simple MCP Gateway implementation for managing MCP servers.

This provides a REST API to interact with MCP servers, specifically
designed for DuckDuckGo search integration with CrewAI.
"""
import asyncio
import json
import os
import uuid
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, status
from loguru import logger
import uvicorn


class MockMCPGateway:
    """
    Mock MCP Gateway for development and testing.
    
    This implementation provides a simplified MCP server interface
    focused on DuckDuckGo search capabilities.
    """
    
    def __init__(self, config_path: str = "/config/servers.json"):
        self.config_path = config_path
        self.servers_config = {}
        self.active_sessions = {}
        self.load_config()
        
    def load_config(self):
        """Load MCP servers configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.servers_config = config.get("servers", {})
                    logger.info(f"Loaded {len(self.servers_config)} MCP server configurations")
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                # Default configuration for DuckDuckGo
                self.servers_config = {
                    "duckduckgo": {
                        "description": "DuckDuckGo search server for web searches",
                        "capabilities": {
                            "tools": {
                                "web_search": {
                                    "description": "Search the web using DuckDuckGo",
                                    "parameters": {
                                        "query": {
                                            "type": "string", 
                                            "description": "Search query"
                                        },
                                        "max_results": {
                                            "type": "integer",
                                            "description": "Maximum number of results to return",
                                            "default": 5
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.servers_config = {}
            
    async def get_servers(self) -> Dict[str, Any]:
        """Get available MCP servers."""
        return self.servers_config
        
    async def connect_server(self, server_name: str) -> Dict[str, str]:
        """Connect to an MCP server."""
        if server_name not in self.servers_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server '{server_name}' not found"
            )
            
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "server_name": server_name,
            "created_at": asyncio.get_event_loop().time()
        }
        
        logger.info(f"Created session {session_id} for server '{server_name}'")
        return {"session_id": session_id, "status": "connected"}
        
    async def disconnect_server(self, server_name: str, session_id: str) -> Dict[str, str]:
        """Disconnect from an MCP server."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Disconnected session {session_id} for server '{server_name}'")
            
        return {"status": "disconnected"}
        
    async def get_server_tools(self, server_name: str) -> Dict[str, Any]:
        """Get available tools for a server."""
        if server_name not in self.servers_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server '{server_name}' not found"
            )
            
        server_config = self.servers_config[server_name]
        tools = []
        
        for tool_name, tool_config in server_config.get("capabilities", {}).get("tools", {}).items():
            tools.append({
                "name": tool_name,
                "description": tool_config.get("description", ""),
                "parameters": tool_config.get("parameters", {})
            })
            
        return {"tools": tools}
        
    async def execute_tool(self, server_name: str, tool_name: str, session_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on an MCP server."""
        if session_id not in self.active_sessions:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session ID"
            )
            
        if server_name != "duckduckgo":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Server '{server_name}' not implemented"
            )
            
        if tool_name != "web_search":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found"
            )
            
        # Mock DuckDuckGo search implementation
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)
        
        if not query:
            return {"result": "Error: Query parameter is required"}
            
        # Simulate search results
        mock_results = [
            {
                "title": f"Search result {i+1} for '{query}'",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is a mock search result snippet for query '{query}'. Result {i+1} contains relevant information."
            }
            for i in range(min(max_results, 3))  # Limit to 3 mock results
        ]
        
        result_text = f"Found {len(mock_results)} results for '{query}':\n\n"
        for i, result in enumerate(mock_results, 1):
            result_text += f"{i}. {result['title']}\n"
            result_text += f"   URL: {result['url']}\n"
            result_text += f"   {result['snippet']}\n\n"
            
        logger.info(f"Executed DuckDuckGo search for query: '{query}', returned {len(mock_results)} results")
        
        return {"result": result_text}


# Initialize the gateway
gateway = MockMCPGateway()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting MCP Gateway")
    yield
    logger.info("Shutting down MCP Gateway")


# Create FastAPI app
app = FastAPI(
    title="MCP Gateway",
    description="Gateway for managing MCP servers",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "active_sessions": len(gateway.active_sessions)}


@app.get("/servers")
async def get_servers():
    """Get available MCP servers."""
    return await gateway.get_servers()


@app.post("/servers/{server_name}/connect")
async def connect_server(server_name: str):
    """Connect to an MCP server."""
    return await gateway.connect_server(server_name)


@app.post("/servers/{server_name}/disconnect")
async def disconnect_server(server_name: str, request: Dict[str, str]):
    """Disconnect from an MCP server."""
    session_id = request.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required"
        )
    return await gateway.disconnect_server(server_name, session_id)


@app.get("/servers/{server_name}/tools")
async def get_server_tools(server_name: str):
    """Get available tools for a server."""
    return await gateway.get_server_tools(server_name)


@app.post("/servers/{server_name}/tools/{tool_name}/execute")
async def execute_tool(server_name: str, tool_name: str, request: Dict[str, Any]):
    """Execute a tool on an MCP server."""
    session_id = request.get("session_id")
    arguments = request.get("arguments", {})
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required"
        )
        
    return await gateway.execute_tool(server_name, tool_name, session_id, arguments)


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        level="INFO",
        colorize=True
    )
    
    # Run the gateway
    host = os.getenv("MCP_GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_GATEWAY_PORT", "8080"))
    
    logger.info(f"Starting MCP Gateway on {host}:{port}")
    uvicorn.run(app, host=host, port=port)