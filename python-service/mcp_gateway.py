"""
MCP Gateway implementation for managing MCP servers like DuckDuckGo.

This service exposes a REST API that allows clients to connect to MCP
servers, inspect their available tools, and execute those tools. It uses the
Model Context Protocol Python toolkit and launches each server as a
subprocess based on configuration in ``/config/servers.json``.
"""

import json
import os
import re
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Match, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, status
from loguru import logger

from mcp import ClientSession
from mcp.transport import SubprocessTransport
from mcp.types import Tool as MCPTool


_ENV_VAR_PATTERN = re.compile(
    r"""
    \$
    (?:
        \{
            (?P<braced_name>[A-Za-z_][A-Za-z0-9_]*)
            (?::(?P<modifier>[-?])(?P<default>[^}]*))?
        \}
        |
        (?P<simple_name>[A-Za-z_][A-Za-z0-9_]*)
    )
    """,
    re.VERBOSE,
)

_LITERAL_DOLLAR_MARKER = "\0"


class MCPGateway:
    """Gateway for managing MCP server subprocesses."""

    def __init__(self, config_path: str = "/config/servers.json"):
        self.config_path = config_path
        self.servers_config: Dict[str, Any] = {}
        # session_id -> {server_name, transport, protocol, client}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        # server_name -> session_id
        self.server_sessions: Dict[str, str] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load server configuration from JSON file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    self.servers_config = config.get("servers", {})
                    logger.info(
                        f"Loaded {len(self.servers_config)} MCP server configurations"
                    )
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                self.servers_config = {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.servers_config = {}

    async def get_servers(self) -> Dict[str, Any]:
        """Return available server configurations."""
        return self.servers_config

    async def connect_server(self, server_name: str) -> Dict[str, str]:
        """Launch and connect to an MCP server."""
        if server_name not in self.servers_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server '{server_name}' not found",
            )

        # Reuse existing session if already connected
        if server_name in self.server_sessions:
            session_id = self.server_sessions[server_name]
            return {"session_id": session_id, "status": "connected"}

        cfg = self.servers_config[server_name]
        command = cfg.get("command")
        args = cfg.get("args", [])
        env_cfg = cfg.get("env", {})
        expanded_env = self._build_environment(env_cfg, server_name)

        try:
            transport = SubprocessTransport(command, args=args, env=expanded_env)
            await transport.start()
            protocol = transport.open_session()
            client = ClientSession(protocol)
            await client.initialize()

            session_id = str(uuid.uuid4())
            self.active_sessions[session_id] = {
                "server_name": server_name,
                "transport": transport,
                "protocol": protocol,
                "client": client,
            }
            self.server_sessions[server_name] = session_id

            logger.info(
                f"Connected to MCP server '{server_name}' with session {session_id}"
            )
            return {"session_id": session_id, "status": "connected"}
        except Exception as e:
            logger.error(f"Failed to connect to server '{server_name}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to connect to server '{server_name}'",
            )

    def _build_environment(
        self, env_cfg: Dict[str, Any], server_name: str
    ) -> Dict[str, str]:
        """Expand environment variables for a server configuration."""

        expanded_env: Dict[str, str] = {}
        missing_vars: Dict[str, Optional[str]] = {}

        for key, raw_value in env_cfg.items():
            if isinstance(raw_value, str):
                expanded_value = self._expand_env_string(raw_value, missing_vars)
            else:
                expanded_value = str(raw_value)
            expanded_env[key] = expanded_value

        if missing_vars:
            missing_details = []
            for var_name, message in missing_vars.items():
                if message:
                    missing_details.append(f"{var_name} ({message})")
                else:
                    missing_details.append(var_name)
            detail = (
                f"Missing required environment variables for server '{server_name}': "
                + ", ".join(sorted(missing_details))
            )
            logger.error(detail)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail,
            )

        return expanded_env

    def _expand_env_string(
        self,
        value: str,
        missing_vars: Dict[str, Optional[str]],
    ) -> str:
        """Expand environment placeholders within a string value."""

        value_with_sentinel = value.replace("$$", _LITERAL_DOLLAR_MARKER)

        def replace(match: Match[str]) -> str:
            var_name = match.group("braced_name") or match.group("simple_name")
            modifier = match.group("modifier")
            default = match.group("default")
            env_val = os.environ.get(var_name)

            if env_val not in (None, ""):
                return env_val

            if modifier == "-":
                default_value = default or ""
                return default_value.replace(_LITERAL_DOLLAR_MARKER, "$")

            message: Optional[str] = None
            if modifier == "?":
                message = (default or "").replace(_LITERAL_DOLLAR_MARKER, "$")

            missing_vars.setdefault(var_name, message)
            return ""

        expanded = _ENV_VAR_PATTERN.sub(replace, value_with_sentinel)
        return expanded.replace(_LITERAL_DOLLAR_MARKER, "$")

    async def disconnect_server(self, server_name: str, session_id: str) -> Dict[str, str]:
        """Disconnect and terminate a server session."""
        session = self.active_sessions.pop(session_id, None)
        self.server_sessions.pop(server_name, None)

        if not session:
            return {"status": "disconnected"}

        transport: SubprocessTransport = session.get("transport")
        protocol = session.get("protocol")
        client: ClientSession = session.get("client")

        # Best effort cleanup
        try:
            await client.close()
        except Exception:
            pass
        try:
            await protocol.close()
        except Exception:
            pass
        try:
            await transport.close()
        except Exception:
            pass

        logger.info(
            f"Disconnected session {session_id} for server '{server_name}'"
        )
        return {"status": "disconnected"}

    async def get_server_tools(self, server_name: str) -> Dict[str, Any]:
        """List tools provided by a connected server."""
        if server_name not in self.server_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server '{server_name}' not connected",
            )

        session_id = self.server_sessions[server_name]
        client: ClientSession = self.active_sessions[session_id]["client"]

        tools: List[MCPTool] = (await client.list_tools()).tools
        tool_list = []
        for tool in tools:
            tool_list.append(
                {
                    "name": tool.name,
                    "description": getattr(tool, "description", ""),
                    "parameters": getattr(tool, "input_schema", {}),
                }
            )

        return {"tools": tool_list}

    async def execute_tool(
        self,
        server_name: str,
        tool_name: str,
        session_id: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a tool on a connected server."""
        session = self.active_sessions.get(session_id)
        if not session or session.get("server_name") != server_name:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found for server '{server_name}'",
            )

        client: ClientSession = session["client"]

        try:
            response = await client.call_tool(tool_name, arguments)
            parts = []
            for item in getattr(response, "content", []):
                text = getattr(item, "text", None)
                if text:
                    parts.append(text)
            result_text = "\n".join(parts) if parts else str(response)
            logger.info(
                f"Executed tool '{tool_name}' on server '{server_name}'"
            )
            return {"result": result_text}
        except Exception as e:
            logger.error(
                f"Error executing tool '{tool_name}' on server '{server_name}': {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing tool '{tool_name}' on server '{server_name}'",
            )


# Initialize the gateway instance
gateway = MCPGateway()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MCP Gateway")
    yield
    logger.info("Shutting down MCP Gateway")


# FastAPI application
app = FastAPI(
    title="MCP Gateway",
    description="Gateway for managing MCP servers",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "active_sessions": len(gateway.active_sessions)}


@app.get("/servers")
async def get_servers():
    """Return available MCP servers."""
    return await gateway.get_servers()


@app.post("/servers/{server_name}/connect")
async def connect_server(server_name: str):
    """Connect to a configured MCP server."""
    return await gateway.connect_server(server_name)


@app.post("/servers/{server_name}/disconnect")
async def disconnect_server(server_name: str, request: Dict[str, str]):
    """Disconnect from a connected MCP server."""
    session_id = request.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required",
        )
    return await gateway.disconnect_server(server_name, session_id)


@app.get("/servers/{server_name}/tools")
async def get_server_tools(server_name: str):
    """List available tools for a server."""
    return await gateway.get_server_tools(server_name)


@app.post("/servers/{server_name}/tools/{tool_name}/execute")
async def execute_tool(server_name: str, tool_name: str, request: Dict[str, Any]):
    """Execute a tool on the specified server."""
    session_id = request.get("session_id")
    arguments = request.get("arguments", {})
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required",
        )
    return await gateway.execute_tool(server_name, tool_name, session_id, arguments)


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        level="INFO",
        colorize=True,
    )

    host = os.getenv("MCP_GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_GATEWAY_PORT", "8811"))
    logger.info(f"Starting MCP Gateway on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

