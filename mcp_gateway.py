#!/usr/bin/env python3
"""
MCP Gateway Implementation for Trainium Job Center

This is a FastAPI-based MCP (Model Context Protocol) gateway that implements
the standard MCP JSON-RPC 2.0 protocol over HTTP streaming transport.

The gateway serves as a central hub for managing MCP servers and handling
client connections using the standard MCP protocol.
"""

import asyncio
import argparse
import json
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger
import httpx

# MCP Protocol Configuration
MCP_PROTOCOL_VERSION = "2025-03-26"
MCP_CLIENT_NAME = "trainium-mcp-gateway"
MCP_CLIENT_VERSION = "1.0.0"

class MCPGateway:
    """MCP Gateway for managing multiple MCP servers and client connections."""
    
    def __init__(self, servers: List[str], transport: str = "streaming", port: int = 8811):
        self.servers = servers
        self.transport = transport
        self.port = port
        self.app = FastAPI(
            title="Trainium MCP Gateway",
            description="Model Context Protocol Gateway for Trainium Job Center",
            version="1.0.0"
        )
        self.setup_routes()
        self.server_configs = {}
        self.active_connections = {}
        
    def setup_routes(self):
        """Setup FastAPI routes for MCP protocol endpoints."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for the MCP Gateway."""
            return {
                "status": "healthy",
                "service": "mcp-gateway",
                "version": MCP_CLIENT_VERSION,
                "transport": self.transport,
                "servers": self.servers,
                "protocol_version": MCP_PROTOCOL_VERSION
            }
        
        @self.app.post("/mcp/initialize")
        async def initialize(request: Request):
            """MCP initialize handshake endpoint."""
            try:
                body = await request.json()
                
                # Validate JSON-RPC 2.0 format
                if not self._validate_jsonrpc(body):
                    raise HTTPException(status_code=400, detail="Invalid JSON-RPC 2.0 format")
                
                # Handle initialize method
                if body.get("method") != "initialize":
                    return self._create_error_response(body.get("id"), -32601, "Method not found")
                
                params = body.get("params", {})
                client_info = params.get("clientInfo", {})
                
                logger.info(f"MCP Initialize request from client: {client_info.get('name', 'unknown')}")
                
                # Return successful initialization response
                response = {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {"listChanged": True}
                        },
                        "serverInfo": {
                            "name": MCP_CLIENT_NAME,
                            "version": MCP_CLIENT_VERSION
                        },
                        "instructions": "Connected to Trainium MCP Gateway"
                    }
                }
                
                return JSONResponse(content=response)
                
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON")
            except Exception as e:
                logger.error(f"Initialize error: {e}")
                raise HTTPException(status_code=500, detail=f"Initialize failed: {str(e)}")
        
        @self.app.post("/mcp/tools/list")
        async def list_tools(request: Request):
            """List available tools from configured MCP servers."""
            try:
                body = await request.json()
                
                if not self._validate_jsonrpc(body):
                    raise HTTPException(status_code=400, detail="Invalid JSON-RPC 2.0 format")
                
                logger.info("MCP Tools list request")
                
                # Mock tools for demonstration - in real implementation, this would
                # query actual MCP servers configured in the gateway
                tools = [
                    {
                        "name": "duckduckgo_search",
                        "description": "Search the web using DuckDuckGo",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "linkedin_search",
                        "description": "Search LinkedIn for job opportunities",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "keywords": {
                                    "type": "string",
                                    "description": "Job search keywords"
                                },
                                "location": {
                                    "type": "string",
                                    "description": "Job location"
                                }
                            },
                            "required": ["keywords"]
                        }
                    }
                ]
                
                response = {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "tools": tools
                    }
                }
                
                return JSONResponse(content=response)
                
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON")
            except Exception as e:
                logger.error(f"Tools list error: {e}")
                raise HTTPException(status_code=500, detail=f"Tools list failed: {str(e)}")
        
        @self.app.post("/mcp/tools/call")
        async def call_tool(request: Request):
            """Execute a tool call through the appropriate MCP server."""
            try:
                body = await request.json()
                
                if not self._validate_jsonrpc(body):
                    raise HTTPException(status_code=400, detail="Invalid JSON-RPC 2.0 format")
                
                params = body.get("params", {})
                tool_name = params.get("name")
                tool_arguments = params.get("arguments", {})
                
                logger.info(f"MCP Tool call: {tool_name} with args: {tool_arguments}")
                
                # Mock tool execution - in real implementation, this would
                # route to the appropriate MCP server based on tool name
                if tool_name == "duckduckgo_search":
                    result = await self._mock_duckduckgo_search(tool_arguments)
                elif tool_name == "linkedin_search":
                    result = await self._mock_linkedin_search(tool_arguments)
                else:
                    return self._create_error_response(body.get("id"), -32601, f"Tool not found: {tool_name}")
                
                response = {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    }
                }
                
                return JSONResponse(content=response)
                
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON")
            except Exception as e:
                logger.error(f"Tool call error: {e}")
                raise HTTPException(status_code=500, detail=f"Tool call failed: {str(e)}")
        
        @self.app.get("/mcp/status")
        async def gateway_status():
            """Get detailed status of the MCP Gateway and connected servers."""
            return {
                "gateway": {
                    "status": "running",
                    "transport": self.transport,
                    "port": self.port,
                    "protocol_version": MCP_PROTOCOL_VERSION
                },
                "servers": {
                    server: {"status": "configured", "transport": self.transport}
                    for server in self.servers
                },
                "active_connections": len(self.active_connections)
            }
    
    def _validate_jsonrpc(self, body: Dict[str, Any]) -> bool:
        """Validate JSON-RPC 2.0 format."""
        return (
            isinstance(body, dict) and
            body.get("jsonrpc") == "2.0" and
            "id" in body and
            "method" in body
        )
    
    def _create_error_response(self, request_id: Any, code: int, message: str) -> JSONResponse:
        """Create a JSON-RPC 2.0 error response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        return JSONResponse(content=response, status_code=400)
    
    async def _mock_duckduckgo_search(self, arguments: Dict[str, Any]) -> str:
        """Mock DuckDuckGo search implementation."""
        query = arguments.get("query", "")
        logger.info(f"Mock DuckDuckGo search for: {query}")
        
        # In a real implementation, this would call the actual DuckDuckGo MCP server
        return f"Mock search results for '{query}': This is a placeholder implementation. In production, this would route to the actual DuckDuckGo MCP server and return real search results."
    
    async def _mock_linkedin_search(self, arguments: Dict[str, Any]) -> str:
        """Mock LinkedIn search implementation."""
        keywords = arguments.get("keywords", "")
        location = arguments.get("location", "")
        logger.info(f"Mock LinkedIn search for: {keywords} in {location}")
        
        # In a real implementation, this would call the actual LinkedIn MCP server
        return f"Mock LinkedIn job search for '{keywords}' in '{location}': This is a placeholder implementation. In production, this would route to the actual LinkedIn MCP server and return job search results."
    
    def run(self):
        """Run the MCP Gateway server."""
        logger.info(f"Starting MCP Gateway on port {self.port}")
        logger.info(f"Configured servers: {', '.join(self.servers)}")
        logger.info(f"Transport: {self.transport}")
        
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )


def main():
    """Main entry point for the MCP Gateway."""
    parser = argparse.ArgumentParser(description="Trainium MCP Gateway")
    parser.add_argument(
        "--servers",
        type=str,
        default="duckduckgo,linkedin-mcp-server",
        help="Comma-separated list of MCP servers to manage"
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="streaming",
        choices=["streaming", "stdio"],
        help="Transport type for MCP communication"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8811,
        help="Port to run the gateway on"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level=args.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Parse servers list
    servers = [s.strip() for s in args.servers.split(",") if s.strip()]
    
    # Create and run gateway
    gateway = MCPGateway(
        servers=servers,
        transport=args.transport,
        port=args.port
    )
    
    try:
        gateway.run()
    except KeyboardInterrupt:
        logger.info("Shutting down MCP Gateway")
    except Exception as e:
        logger.error(f"Gateway error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()