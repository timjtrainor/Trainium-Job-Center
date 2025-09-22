# MCP (Model Context Protocol) Transport Layer

This module provides the foundational transport abstraction and basic MCP protocol handling for the Trainium Job Center application.

## Overview

The MCP transport layer implements:

- **Transport Abstraction**: Abstract base class with stdio and HTTP streaming implementations
- **JSON-RPC Message Models**: Validated message structures using dataclasses
- **Exception Hierarchy**: Comprehensive error handling for transport, connection, and protocol failures  
- **Structured Logging**: JSON-formatted logging with correlation IDs and context

## Architecture

```
app/services/mcp/
├── __init__.py           # Package exports
├── mcp_transport.py      # Transport implementations
├── mcp_models.py         # JSON-RPC message models
├── mcp_exceptions.py     # Exception hierarchy
├── mcp_logging.py        # Structured logging
└── README.md            # This file
```

## Key Components

### Transport Layer (`mcp_transport.py`)

- `MCPTransport`: Abstract base class defining the transport interface
- `StdioTransport`: Stdio-based JSON-RPC communication
- `StreamingTransport`: HTTP streaming transport (basic implementation)

### Message Models (`mcp_models.py`)

- `JsonRpcRequest/Response`: Core JSON-RPC 2.0 message structures
- `InitializeRequest/Response`: MCP protocol initialization messages
- `MCPCapabilities`: MCP capability declarations
- Helper functions for creating common responses

### Exception Handling (`mcp_exceptions.py`)

- `MCPError`: Base exception class
- Specific exceptions: `ConnectionError`, `HandshakeError`, `TransportError`, etc.
- Helper functions for creating common error scenarios

### Logging (`mcp_logging.py`)

- `StructuredFormatter`: JSON log formatter
- `MCPLoggerAdapter`: Context-aware logger
- Helper functions for standardized operation logging

## Usage Examples

### Basic Transport Usage

```python
from app.services.mcp import StdioTransport, JsonRpcRequest

# Create and connect transport
transport = StdioTransport()
await transport.connect()

# Send initialize request
request = JsonRpcRequest(method="initialize", id=1, params={...})
await transport.send_message(request.to_dict())

# Receive response
response = await transport.receive_message()

await transport.disconnect()
```

### Logging with Context

```python
from app.services.mcp.mcp_logging import configure_logging, get_mcp_logger

# Configure structured logging
configure_logging("INFO", structured=True)

# Get logger with context
logger = get_mcp_logger(
    correlation_id="req-123",
    transport_type="stdio"
)

logger.info("MCP operation started")
```

### Error Handling

```python
from app.services.mcp.mcp_exceptions import connection_failed, MCPError

try:
    await transport.connect()
except Exception as e:
    # Create structured MCP error
    mcp_error = connection_failed("http://gateway:8811", e)
    logger.error(f"Connection failed: {mcp_error}")
    raise mcp_error
```

## Configuration

Add these environment variables to configure MCP:

```env
# Enable MCP functionality
MCP_ENABLED=true

# Transport configuration  
MCP_TRANSPORT_TYPE=stdio  # or 'streaming'
MCP_GATEWAY_URL=http://mcp-gateway:8811
MCP_PROTOCOL_VERSION=2025-03-26

# Client information
MCP_CLIENT_NAME=trainium-job-center
MCP_CLIENT_VERSION=1.0.0

# Logging and timeouts
MCP_LOG_LEVEL=INFO
MCP_CONNECTION_TIMEOUT=30
```

## Dependencies

The implementation uses only Python standard library features:

- `asyncio` - Async I/O operations
- `json` - JSON serialization  
- `dataclasses` - Message model structures
- `logging` - Structured logging
- `abc` - Abstract base classes

Optional dependencies for enhanced functionality:

- `structlog` - Enhanced structured logging
- `aiohttp` - Full HTTP streaming transport implementation

## Testing

Run the test suite:

```bash
cd python-service
python -m unittest discover tests/mcp -v
```

Test coverage includes:
- Transport connection/disconnection
- Message serialization/deserialization  
- Exception handling and propagation
- Logging functionality and formatting

## Protocol Compliance

This implementation follows:

- **JSON-RPC 2.0** specification for message format
- **MCP Protocol** version 2025-03-26 for initialization handshake
- **Transport-agnostic** design supporting stdio and HTTP streaming

## Future Enhancements

- Full HTTP streaming implementation with aiohttp
- Connection pooling and retry logic
- Protocol capability negotiation
- Authentication and authorization support
- Performance metrics and monitoring

## Error Codes

Standard JSON-RPC error codes:
- `-32700`: Parse error
- `-32600`: Invalid request  
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

MCP-specific error codes:
- `-32000`: Handshake error
- `-32001`: Transport error  
- `-32002`: Protocol error