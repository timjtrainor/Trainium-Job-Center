"""Tests for MCP exceptions.

This module contains tests for the MCP exception hierarchy and helper functions.
"""

import unittest

# Import the modules we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.mcp.mcp_exceptions import (
    MCPError,
    ConnectionError,
    HandshakeError,
    TransportError,
    ProtocolError,
    SerializationError,
    TimeoutError,
    AuthenticationError,
    connection_failed,
    handshake_failed,
    transport_failed,
    protocol_violation,
    serialization_failed,
    operation_timeout
)


class TestMCPError(unittest.TestCase):
    """Test the base MCPError class."""
    
    def test_basic_creation(self):
        """Test basic error creation."""
        error = MCPError("Test error")
        
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.message, "Test error")
        self.assertIsNone(error.details)
    
    def test_creation_with_details(self):
        """Test error creation with details."""
        details = {"key": "value", "code": 123}
        error = MCPError("Test error", details)
        
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.details, details)
        self.assertIn("details:", str(error))
    
    def test_inheritance(self):
        """Test that MCPError inherits from Exception."""
        error = MCPError("Test error")
        self.assertIsInstance(error, Exception)


class TestConnectionError(unittest.TestCase):
    """Test the ConnectionError class."""
    
    def test_basic_creation(self):
        """Test basic connection error creation."""
        error = ConnectionError("Connection failed")
        
        self.assertEqual(error.message, "Connection failed")
        self.assertIsNone(error.gateway_url)
        self.assertIsInstance(error, MCPError)
    
    def test_creation_with_gateway_url(self):
        """Test connection error creation with gateway URL."""
        error = ConnectionError("Connection failed", "http://gateway:8811")
        
        self.assertEqual(error.gateway_url, "http://gateway:8811")
        self.assertIn("gateway:", str(error))
    
    def test_creation_with_details(self):
        """Test connection error creation with details."""
        details = {"timeout": 30}
        error = ConnectionError("Connection failed", details=details)
        
        self.assertEqual(error.details, details)


class TestHandshakeError(unittest.TestCase):
    """Test the HandshakeError class."""
    
    def test_basic_creation(self):
        """Test basic handshake error creation."""
        error = HandshakeError("Handshake failed")
        
        self.assertEqual(error.message, "Handshake failed")
        self.assertIsNone(error.protocol_version)
        self.assertIsInstance(error, MCPError)
    
    def test_creation_with_protocol_version(self):
        """Test handshake error creation with protocol version."""
        error = HandshakeError("Version mismatch", "2024-01-01")
        
        self.assertEqual(error.protocol_version, "2024-01-01")
        self.assertIn("protocol version:", str(error))


class TestTransportError(unittest.TestCase):
    """Test the TransportError class."""
    
    def test_basic_creation(self):
        """Test basic transport error creation."""
        error = TransportError("Transport failed")
        
        self.assertEqual(error.message, "Transport failed")
        self.assertIsNone(error.transport_type)
        self.assertIsInstance(error, MCPError)
    
    def test_creation_with_transport_type(self):
        """Test transport error creation with transport type."""
        error = TransportError("Send failed", "stdio")
        
        self.assertEqual(error.transport_type, "stdio")
        self.assertIn("transport:", str(error))


class TestProtocolError(unittest.TestCase):
    """Test the ProtocolError class."""
    
    def test_basic_creation(self):
        """Test basic protocol error creation."""
        error = ProtocolError("Protocol violation")
        
        self.assertEqual(error.message, "Protocol violation")
        self.assertIsNone(error.method)
        self.assertIsInstance(error, MCPError)
    
    def test_creation_with_method(self):
        """Test protocol error creation with method."""
        error = ProtocolError("Invalid params", "initialize")
        
        self.assertEqual(error.method, "initialize")
        self.assertIn("method:", str(error))


class TestSerializationError(unittest.TestCase):
    """Test the SerializationError class."""
    
    def test_basic_creation(self):
        """Test basic serialization error creation."""
        error = SerializationError("Serialization failed")
        
        self.assertEqual(error.message, "Serialization failed")
        self.assertIsNone(error.data)
        self.assertIsInstance(error, MCPError)
    
    def test_creation_with_data(self):
        """Test serialization error creation with data."""
        data = {"invalid": "json"}
        error = SerializationError("JSON error", data)
        
        self.assertEqual(error.data, data)
        self.assertIn("data:", str(error))


class TestTimeoutError(unittest.TestCase):
    """Test the TimeoutError class."""
    
    def test_basic_creation(self):
        """Test basic timeout error creation."""
        error = TimeoutError("Operation timed out")
        
        self.assertEqual(error.message, "Operation timed out")
        self.assertIsNone(error.timeout_seconds)
        self.assertIsInstance(error, MCPError)
    
    def test_creation_with_timeout(self):
        """Test timeout error creation with timeout value."""
        error = TimeoutError("Connect timed out", 30.0)
        
        self.assertEqual(error.timeout_seconds, 30.0)
        self.assertIn("timeout:", str(error))


class TestAuthenticationError(unittest.TestCase):
    """Test the AuthenticationError class."""
    
    def test_basic_creation(self):
        """Test basic authentication error creation."""
        error = AuthenticationError("Auth failed")
        
        self.assertEqual(error.message, "Auth failed")
        self.assertIsNone(error.auth_method)
        self.assertIsInstance(error, MCPError)
    
    def test_creation_with_auth_method(self):
        """Test authentication error creation with auth method."""
        error = AuthenticationError("Token invalid", "bearer")
        
        self.assertEqual(error.auth_method, "bearer")
        self.assertIn("auth method:", str(error))


class TestHelperFunctions(unittest.TestCase):
    """Test exception helper functions."""
    
    def test_connection_failed(self):
        """Test connection_failed helper."""
        underlying = ValueError("Socket error")
        error = connection_failed("http://gateway:8811", underlying)
        
        self.assertIsInstance(error, ConnectionError)
        self.assertEqual(error.gateway_url, "http://gateway:8811")
        self.assertIn("Socket error", str(error))
        self.assertIsNotNone(error.details)
    
    def test_handshake_failed(self):
        """Test handshake_failed helper."""
        error = handshake_failed("Version mismatch", "2024-01-01")
        
        self.assertIsInstance(error, HandshakeError)
        self.assertEqual(error.protocol_version, "2024-01-01")
        self.assertIn("Version mismatch", str(error))
    
    def test_handshake_failed_default_version(self):
        """Test handshake_failed helper with default version."""
        error = handshake_failed("Capability error")
        
        self.assertEqual(error.protocol_version, "2025-03-26")
    
    def test_transport_failed(self):
        """Test transport_failed helper."""
        underlying = IOError("Pipe broken")
        error = transport_failed("stdio", "send", underlying)
        
        self.assertIsInstance(error, TransportError)
        self.assertEqual(error.transport_type, "stdio")
        self.assertIn("send", str(error))
        self.assertIn("Pipe broken", str(error))
        self.assertIsNotNone(error.details)
    
    def test_protocol_violation(self):
        """Test protocol_violation helper."""
        error = protocol_violation("initialize", "Missing params")
        
        self.assertIsInstance(error, ProtocolError)
        self.assertEqual(error.method, "initialize")
        self.assertIn("Missing params", str(error))
    
    def test_serialization_failed(self):
        """Test serialization_failed helper."""
        data = {"circular": None}
        data["circular"] = data  # Create circular reference
        underlying = ValueError("Circular reference")
        
        error = serialization_failed("encode", data, underlying)
        
        self.assertIsInstance(error, SerializationError)
        self.assertEqual(error.data, data)
        self.assertIn("encode", str(error))
        self.assertIn("Circular reference", str(error))
        self.assertIsNotNone(error.details)
    
    def test_operation_timeout(self):
        """Test operation_timeout helper."""
        error = operation_timeout("connect", 30.0)
        
        self.assertIsInstance(error, TimeoutError)
        self.assertEqual(error.timeout_seconds, 30.0)
        self.assertIn("connect", str(error))
        self.assertIsNotNone(error.details)


class TestExceptionChaining(unittest.TestCase):
    """Test exception chaining and inheritance."""
    
    def test_all_inherit_from_mcp_error(self):
        """Test that all custom exceptions inherit from MCPError."""
        exceptions = [
            ConnectionError("test"),
            HandshakeError("test"),
            TransportError("test"),
            ProtocolError("test"),
            SerializationError("test"),
            TimeoutError("test"),
            AuthenticationError("test")
        ]
        
        for exc in exceptions:
            with self.subTest(exception=exc.__class__.__name__):
                self.assertIsInstance(exc, MCPError)
                self.assertIsInstance(exc, Exception)
    
    def test_exception_can_be_caught_as_mcp_error(self):
        """Test that specific exceptions can be caught as MCPError."""
        def raise_connection_error():
            raise ConnectionError("Connection failed")
        
        with self.assertRaises(MCPError):
            raise_connection_error()
    
    def test_exception_details_preservation(self):
        """Test that exception details are preserved through the hierarchy."""
        details = {"code": 123, "context": "test"}
        error = TransportError("Test error", "stdio", details)
        
        # Should be catchable as MCPError while preserving details
        try:
            raise error
        except MCPError as caught:
            self.assertEqual(caught.details, details)
            self.assertEqual(caught.message, "Test error")


if __name__ == '__main__':
    unittest.main()