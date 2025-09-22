"""MCP Custom Exceptions.

This module defines the exception hierarchy for MCP operations,
providing specific error types for different failure scenarios.
"""

from typing import Optional, Any


class MCPError(Exception):
    """Base exception for MCP operations.
    
    All MCP-specific exceptions inherit from this base class.
    """
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class ConnectionError(MCPError):
    """Gateway connection failures.
    
    Raised when there are issues establishing or maintaining
    connections to the MCP gateway.
    """
    
    def __init__(self, message: str, gateway_url: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message, details)
        self.gateway_url = gateway_url
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.gateway_url:
            return f"{base_msg} (gateway: {self.gateway_url})"
        return base_msg


class HandshakeError(MCPError):
    """MCP protocol handshake failures.
    
    Raised when the MCP initialization/handshake process fails,
    such as protocol version mismatches or capability negotiation issues.
    """
    
    def __init__(self, message: str, protocol_version: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message, details)
        self.protocol_version = protocol_version
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.protocol_version:
            return f"{base_msg} (protocol version: {self.protocol_version})"
        return base_msg


class TransportError(MCPError):
    """Transport layer failures.
    
    Raised when there are issues with the underlying transport
    mechanism (stdio, HTTP streaming, etc.).
    """
    
    def __init__(self, message: str, transport_type: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message, details)
        self.transport_type = transport_type
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.transport_type:
            return f"{base_msg} (transport: {self.transport_type})"
        return base_msg


class ProtocolError(MCPError):
    """MCP protocol-level errors.
    
    Raised when there are violations of the MCP protocol specification,
    such as invalid message formats or unexpected message sequences.
    """
    
    def __init__(self, message: str, method: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message, details)
        self.method = method
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.method:
            return f"{base_msg} (method: {self.method})"
        return base_msg


class SerializationError(MCPError):
    """Message serialization/deserialization errors.
    
    Raised when there are issues converting messages to/from JSON
    or validating message structure.
    """
    
    def __init__(self, message: str, data: Optional[Any] = None, details: Optional[Any] = None):
        super().__init__(message, details)
        self.data = data
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.data:
            return f"{base_msg} (data: {repr(self.data)[:100]}...)"
        return base_msg


class TimeoutError(MCPError):
    """Operation timeout errors.
    
    Raised when MCP operations exceed their timeout limits.
    """
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, details: Optional[Any] = None):
        super().__init__(message, details)
        self.timeout_seconds = timeout_seconds
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.timeout_seconds:
            return f"{base_msg} (timeout: {self.timeout_seconds}s)"
        return base_msg


class AuthenticationError(MCPError):
    """Authentication and authorization errors.
    
    Raised when there are issues with MCP authentication
    or insufficient permissions for requested operations.
    """
    
    def __init__(self, message: str, auth_method: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message, details)
        self.auth_method = auth_method
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.auth_method:
            return f"{base_msg} (auth method: {self.auth_method})"
        return base_msg


# Convenience functions for creating common exceptions

def connection_failed(gateway_url: str, underlying_error: Exception) -> ConnectionError:
    """Create a ConnectionError for failed gateway connections."""
    return ConnectionError(
        f"Failed to connect to MCP gateway: {underlying_error}",
        gateway_url=gateway_url,
        details={"underlying_error": str(underlying_error)}
    )


def handshake_failed(reason: str, protocol_version: str = "2025-03-26") -> HandshakeError:
    """Create a HandshakeError for failed MCP handshakes."""
    return HandshakeError(
        f"MCP handshake failed: {reason}",
        protocol_version=protocol_version
    )


def transport_failed(transport_type: str, operation: str, underlying_error: Exception) -> TransportError:
    """Create a TransportError for transport operation failures."""
    return TransportError(
        f"Transport operation '{operation}' failed: {underlying_error}",
        transport_type=transport_type,
        details={"operation": operation, "underlying_error": str(underlying_error)}
    )


def protocol_violation(method: str, reason: str) -> ProtocolError:
    """Create a ProtocolError for MCP protocol violations."""
    return ProtocolError(
        f"Protocol violation in method '{method}': {reason}",
        method=method
    )


def serialization_failed(operation: str, data: Any, underlying_error: Exception) -> SerializationError:
    """Create a SerializationError for serialization failures."""
    return SerializationError(
        f"Serialization {operation} failed: {underlying_error}",
        data=data,
        details={"operation": operation, "underlying_error": str(underlying_error)}
    )


def operation_timeout(operation: str, timeout_seconds: float) -> TimeoutError:
    """Create a TimeoutError for operation timeouts."""
    return TimeoutError(
        f"Operation '{operation}' timed out",
        timeout_seconds=timeout_seconds,
        details={"operation": operation}
    )