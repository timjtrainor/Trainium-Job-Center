"""
Helper utilities for configuring MCP Gateway access across crews.

Allows overriding the default Docker service URL when running the Python
service outside of the Compose network (e.g., local dev).
"""

import os
from typing import List, Dict, Any

_DEFAULT_URL = "http://mcp-gateway:8811/mcp/"
_DEFAULT_TRANSPORT = "streamable-http"


def get_mcp_server_config() -> List[Dict[str, Any]]:
    """
    Build the MCP server configuration with environment overrides.

    Env vars:
        MCP_GATEWAY_URL: Full base URL to the MCP endpoint (default docker service)
        MCP_GATEWAY_TRANSPORT: Transport mode expected by MCPServerAdapter
    """
    url = os.getenv("MCP_GATEWAY_URL", _DEFAULT_URL).strip()
    if not url:
        url = _DEFAULT_URL

    # Ensure trailing slash because the adapter expects /mcp/ style path
    if not url.endswith("/"):
        url = f"{url}/"

    transport = os.getenv("MCP_GATEWAY_TRANSPORT", _DEFAULT_TRANSPORT).strip() or _DEFAULT_TRANSPORT

    return [
        {
            "url": url,
            "transport": transport,
            "headers": {
                "Accept": "application/json, text/event-stream"
            },
        }
    ]

