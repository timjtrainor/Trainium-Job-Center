"""MCP (Model Context Protocol) Transport Layer.

This package provides the foundational transport abstraction and basic MCP
protocol handling for the Trainium Job Center application.

Key Components:
- Transport abstractions (stdio, HTTP streaming)
- JSON-RPC message models and validation
- Custom exception hierarchy
- Structured logging configuration

Usage:
    from app.services.mcp import StdioTransport, JsonRpcRequest
    from app.services.mcp.mcp_logging import configure_logging
    
    # Configure logging
    configure_logging("INFO")
    
    # Create transport
    transport = StdioTransport()
    await transport.connect()
    
    # Send message
    request = JsonRpcRequest(method="initialize", id=1)
    await transport.send_message(request.to_dict())
"""

from .mcp_transport import MCPTransport, StdioTransport, StreamingTransport
from .mcp_models import (
    JsonRpcRequest,
    JsonRpcResponse,
    JsonRpcError,
    InitializeRequest,
    InitializeResponse,
    MCPCapabilities,
    ClientInfo,
    JsonRpcErrorCodes,
    create_error_response,
    create_success_response,
    ToolInfo,
    ToolListResponse,
    ToolCallRequest,
    ToolCallResponse
)
from .mcp_exceptions import (
    MCPError,
    ConnectionError,
    HandshakeError,
    TransportError,
    ProtocolError,
    SerializationError,
    TimeoutError,
    AuthenticationError,
    ToolExecutionError,
    connection_failed,
    handshake_failed,
    transport_failed,
    protocol_violation,
    serialization_failed,
    operation_timeout,
    tool_execution_failed
)
from .mcp_logging import (
    configure_logging,
    get_mcp_logger,
    MCPLoggerAdapter,
    log_transport_operation,
    log_message_exchange,
    log_handshake_event
)
from .mcp_protocol import (
    MCPProtocol
)
from .mcp_session import (
    MCPSession,
    create_mcp_session
)
from .mcp_tools import (
    MCPToolManager,
    ToolDiscoveryService
)
from .mcp_results import (
    ResultNormalizer
)

__version__ = "1.0.0"
__author__ = "Trainium Job Center"

__all__ = [
    # Transport classes
    "MCPTransport",
    "StdioTransport", 
    "StreamingTransport",
    
    # Message models
    "JsonRpcRequest",
    "JsonRpcResponse",
    "JsonRpcError",
    "InitializeRequest",
    "InitializeResponse",
    "MCPCapabilities",
    "ClientInfo",
    "JsonRpcErrorCodes",
    "create_error_response",
    "create_success_response",
    
    # Tool models
    "ToolInfo",
    "ToolListResponse", 
    "ToolCallRequest",
    "ToolCallResponse",
    
    # Exceptions
    "MCPError",
    "ConnectionError",
    "HandshakeError", 
    "TransportError",
    "ProtocolError",
    "SerializationError",
    "TimeoutError",
    "AuthenticationError",
    "ToolExecutionError",
    "connection_failed",
    "handshake_failed",
    "transport_failed",
    "protocol_violation",
    "serialization_failed",
    "operation_timeout",
    "tool_execution_failed",
    
    # Logging
    "configure_logging",
    "get_mcp_logger",
    "MCPLoggerAdapter",
    "log_transport_operation",
    "log_message_exchange",
    "log_handshake_event",
    
    # Protocol and session management
    "MCPProtocol",
    "MCPSession",
    "create_mcp_session",
    
    # Tool management
    "MCPToolManager",
    "ToolDiscoveryService",
    "ResultNormalizer"
]