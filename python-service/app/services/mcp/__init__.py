"""MCP (Model Context Protocol) Integration Package.

This package provides a complete implementation of the Model Context Protocol
for integration with MCP gateways and tool execution.

Key Components:
- Transport abstractions (stdio, HTTP streaming)
- Protocol handling and session management
- Tool discovery and execution
- Main gateway adapter (Phase 4)
- Configuration management and health monitoring
- JSON-RPC message models and validation
- Custom exception hierarchy
- Structured logging configuration

Usage:
    from app.services.mcp import MCPConfig, MCPGatewayAdapter
    
    # Create adapter from environment configuration
    adapter = MCPConfig.from_environment()
    
    # Use as context manager
    async with adapter as gateway:
        tools = await gateway.list_tools()
        result = await gateway.execute_tool("my_tool", {"arg": "value"})
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
    ConfigurationError,
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
# Phase 4 - Main adapter and configuration
from .mcp_adapter import MCPGatewayAdapter
from .mcp_config import MCPConfig, ConfigurationError
from .mcp_health import MCPHealthMonitor, HealthCheckResult, MetricSnapshot, HealthCheckRegistry

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
    "ConfigurationError",
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
    "ResultNormalizer",
    
    # Phase 4 - Main adapter and configuration
    "MCPGatewayAdapter",
    "MCPConfig",
    "MCPHealthMonitor",
    "HealthCheckResult",
    "MetricSnapshot",
    "HealthCheckRegistry"
]