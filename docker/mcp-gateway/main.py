#!/usr/bin/env python3
"""
MCP Gateway Server

This server provides a gateway for Model Context Protocol (MCP) servers,
allowing CrewAI agents to interact with various MCP-enabled tools and services.

Currently supports:
- DuckDuckGo search via duckduckgo-mcp-server
- Extensible architecture for additional MCP servers
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Gateway",
    description="Gateway for Model Context Protocol servers",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MCP_SERVERS_CONFIG = {
    "duckduckgo": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-duckduckgo@latest"],
        "env": {},
        "description": "DuckDuckGo search MCP server"
    }
    # Future MCP servers can be added here
}

# Global state
running_servers: Dict[str, subprocess.Popen] = {}
server_ports: Dict[str, int] = {}

class MCPRequest(BaseModel):
    """Request model for MCP operations"""
    server: str = Field(description="MCP server identifier")
    method: str = Field(description="MCP method to call")
    params: Dict[str, Any] = Field(default_factory=dict, description="Method parameters")

class MCPResponse(BaseModel):
    """Response model for MCP operations"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    servers: Dict[str, str]

def get_next_port(start_port: int = 3001) -> int:
    """Get the next available port"""
    import socket
    port = start_port
    while port < start_port + 100:  # Check 100 ports max
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
        port += 1
    raise RuntimeError("No available ports found")

async def start_mcp_server(server_name: str) -> bool:
    """Start an MCP server if not already running"""
    if server_name in running_servers:
        # Check if process is still alive
        if running_servers[server_name].poll() is None:
            return True
        else:
            # Process died, remove it
            del running_servers[server_name]
            if server_name in server_ports:
                del server_ports[server_name]

    if server_name not in MCP_SERVERS_CONFIG:
        logger.error(f"Unknown MCP server: {server_name}")
        return False

    config = MCP_SERVERS_CONFIG[server_name]
    
    try:
        # Assign a port for this server
        port = get_next_port()
        server_ports[server_name] = port
        
        # Set up environment
        env = os.environ.copy()
        env.update(config.get("env", {}))
        env["PORT"] = str(port)
        
        # Start the server process
        process = subprocess.Popen(
            [config["command"]] + config["args"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent
        )
        
        running_servers[server_name] = process
        logger.info(f"Started MCP server '{server_name}' on port {port}")
        
        # Give the server a moment to start
        await asyncio.sleep(2)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to start MCP server '{server_name}': {e}")
        return False

async def stop_mcp_server(server_name: str) -> bool:
    """Stop an MCP server"""
    if server_name not in running_servers:
        return True
    
    try:
        process = running_servers[server_name]
        process.terminate()
        
        # Wait for graceful shutdown
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        
        del running_servers[server_name]
        if server_name in server_ports:
            del server_ports[server_name]
        
        logger.info(f"Stopped MCP server '{server_name}'")
        return True
        
    except Exception as e:
        logger.error(f"Failed to stop MCP server '{server_name}': {e}")
        return False

async def call_mcp_server(server_name: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Call a method on an MCP server"""
    if server_name not in running_servers:
        if not await start_mcp_server(server_name):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to start MCP server '{server_name}'"
            )
    
    if server_name not in server_ports:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MCP server '{server_name}' port not available"
        )
    
    port = server_ports[server_name]
    url = f"http://localhost:{port}/rpc"
    
    # Prepare JSON-RPC request
    rpc_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=rpc_request,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    except httpx.RequestError as e:
        logger.error(f"Request error calling MCP server '{server_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to communicate with MCP server '{server_name}'"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling MCP server '{server_name}': {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"MCP server '{server_name}' returned error: {e.response.text}"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    server_status = {}
    for server_name in MCP_SERVERS_CONFIG.keys():
        if server_name in running_servers:
            process = running_servers[server_name]
            if process.poll() is None:
                server_status[server_name] = "running"
            else:
                server_status[server_name] = "stopped"
        else:
            server_status[server_name] = "not_started"
    
    return HealthResponse(
        status="healthy",
        servers=server_status
    )

@app.get("/servers")
async def list_servers():
    """List available MCP servers"""
    return {
        "servers": {
            name: {
                "description": config["description"],
                "status": "running" if name in running_servers and running_servers[name].poll() is None else "stopped"
            }
            for name, config in MCP_SERVERS_CONFIG.items()
        }
    }

@app.post("/servers/{server_name}/start")
async def start_server(server_name: str):
    """Start a specific MCP server"""
    if server_name not in MCP_SERVERS_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown MCP server: {server_name}"
        )
    
    success = await start_mcp_server(server_name)
    if success:
        return {"message": f"MCP server '{server_name}' started successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to start MCP server '{server_name}'"
        )

@app.post("/servers/{server_name}/stop")
async def stop_server(server_name: str):
    """Stop a specific MCP server"""
    success = await stop_mcp_server(server_name)
    if success:
        return {"message": f"MCP server '{server_name}' stopped successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to stop MCP server '{server_name}'"
        )

@app.post("/call", response_model=MCPResponse)
async def call_mcp_method(request: MCPRequest):
    """Call a method on an MCP server"""
    try:
        result = await call_mcp_server(request.server, request.method, request.params)
        return MCPResponse(success=True, result=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error calling MCP method: {e}")
        return MCPResponse(success=False, error=str(e))

@app.on_event("startup")
async def startup_event():
    """Start default MCP servers on startup"""
    logger.info("Starting MCP Gateway...")
    
    # Start DuckDuckGo server by default
    await start_mcp_server("duckduckgo")

@app.on_event("shutdown") 
async def shutdown_event():
    """Stop all MCP servers on shutdown"""
    logger.info("Shutting down MCP Gateway...")
    
    for server_name in list(running_servers.keys()):
        await stop_mcp_server(server_name)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "3000")),
        log_level="info"
    )