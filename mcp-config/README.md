# MCP Configuration

This directory contains configuration files for the MCP (Model Context Protocol) Gateway.

## Files

- `servers.json` - Configuration for MCP servers managed by the gateway
- `README.md` - This documentation file

## Server Configuration

The `servers.json` file defines the MCP servers that the gateway will manage:

- **duckduckgo**: Web search capabilities using DuckDuckGo
- **linkedin-mcp-server**: LinkedIn job search and networking features

## Usage

The MCP Gateway reads these configuration files on startup to:
1. Initialize connections to configured MCP servers
2. Route tool calls to appropriate servers
3. Manage server lifecycle and health monitoring

## Protocol

The gateway implements MCP (Model Context Protocol) JSON-RPC 2.0 over HTTP streaming transport, providing standardized endpoints for:

- `/mcp/initialize` - Protocol handshake
- `/mcp/tools/list` - Tool discovery
- `/mcp/tools/call` - Tool execution
- `/health` - Health monitoring