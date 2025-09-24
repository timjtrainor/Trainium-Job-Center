"""Tests for MCP transport layer.

This module contains tests for the transport abstraction and implementations.
Tests use Python's built-in unittest and asyncio support.
"""

import asyncio
import json
import sys
import unittest
from unittest.mock import Mock, patch, AsyncMock
from io import StringIO

# Import the modules we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.mcp.mcp_transport import MCPTransport, StdioTransport, StreamingTransport
from app.services.mcp.mcp_exceptions import ConnectionError as MCPConnectionError, TransportError


class TestMCPTransport(unittest.TestCase):
    """Test the abstract MCPTransport base class."""
    
    def test_abstract_methods(self):
        """Test that MCPTransport cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            MCPTransport()
    
    def test_connection_state(self):
        """Test connection state tracking."""
        # Create a minimal concrete implementation for testing
        class TestTransport(MCPTransport):
            async def connect(self): pass
            async def disconnect(self): pass
            async def send_message(self, message): pass
            async def receive_message(self): pass
        
        transport = TestTransport()
        self.assertFalse(transport.is_connected())
        
        transport._connected = True
        self.assertTrue(transport.is_connected())


class TestStdioTransport(unittest.IsolatedAsyncioTestCase):
    """Test the StdioTransport implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.transport = StdioTransport()
    
    def test_initialization(self):
        """Test transport initialization."""
        self.assertFalse(self.transport.is_connected())
        self.assertIsNone(self.transport._stdin_reader)
        self.assertIsNone(self.transport._stdout_writer)
    
    @patch('asyncio.get_event_loop')
    @patch('asyncio.StreamReader')
    @patch('asyncio.StreamReaderProtocol')
    @patch('asyncio.StreamWriter')
    async def test_connect_success(self, mock_writer, mock_protocol, mock_reader, mock_loop):
        """Test successful stdio connection."""
        # Mock the asyncio components
        mock_loop_instance = Mock()
        mock_loop.return_value = mock_loop_instance
        
        mock_reader_instance = Mock()
        mock_reader.return_value = mock_reader_instance
        
        mock_protocol_instance = Mock()
        mock_protocol.return_value = mock_protocol_instance
        
        mock_writer_instance = Mock()
        mock_writer.return_value = mock_writer_instance
        
        # Mock the loop methods
        mock_loop_instance.connect_read_pipe = AsyncMock()
        mock_loop_instance.connect_write_pipe = AsyncMock(
            return_value=(Mock(), Mock())
        )
        
        # Test connection
        await self.transport.connect()
        
        # Verify connection state
        self.assertTrue(self.transport.is_connected())
        self.assertIsNotNone(self.transport._stdin_reader)
        self.assertIsNotNone(self.transport._stdout_writer)
    
    @patch('asyncio.get_event_loop')
    async def test_connect_failure(self, mock_loop):
        """Test failed stdio connection."""
        # Mock the loop to raise an exception
        mock_loop.side_effect = Exception("Connection failed")
        
        # Test connection failure
        with self.assertRaises(Exception):
            await self.transport.connect()
        
        # Verify connection state remains false
        self.assertFalse(self.transport.is_connected())
    
    async def test_send_message_not_connected(self):
        """Test sending message when not connected."""
        message = {"test": "message"}
        
        with self.assertRaises(Exception):
            await self.transport.send_message(message)
    
    async def test_receive_message_not_connected(self):
        """Test receiving message when not connected."""
        with self.assertRaises(Exception):
            await self.transport.receive_message()
    
    async def test_disconnect(self):
        """Test transport disconnection."""
        # Mock a connected state
        mock_writer = Mock()
        mock_writer.close = Mock()
        mock_writer.wait_closed = AsyncMock()
        
        self.transport._connected = True
        self.transport._stdout_writer = mock_writer
        self.transport._stdin_reader = Mock()
        
        # Test disconnection
        await self.transport.disconnect()
        
        # Verify state cleanup
        self.assertFalse(self.transport.is_connected())
        self.assertIsNone(self.transport._stdin_reader)
        self.assertIsNone(self.transport._stdout_writer)
        mock_writer.close.assert_called_once()
        mock_writer.wait_closed.assert_called_once()


class TestStreamingTransport(unittest.IsolatedAsyncioTestCase):
    """Test the StreamingTransport implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.transport = StreamingTransport("http://test-gateway:8811")
    
    def test_initialization(self):
        """Test transport initialization."""
        self.assertEqual(self.transport.gateway_url, "http://test-gateway:8811")
        self.assertFalse(self.transport.is_connected())
        self.assertIsNone(self.transport._session)
    
    async def test_connect_success(self):
        """Test successful streaming connection."""
        # Test connection (placeholder implementation)
        await self.transport.connect()
        
        # Verify connection state
        self.assertTrue(self.transport.is_connected())
    
    async def test_send_message_not_connected(self):
        """Test sending message when not connected."""
        message = {"test": "message"}
        
        with self.assertRaises(Exception):
            await self.transport.send_message(message)
    
    async def test_receive_message_not_connected(self):
        """Test receiving message when not connected."""
        with self.assertRaises(Exception):
            await self.transport.receive_message()
    
    async def test_send_message_connected(self):
        """Test sending message when connected."""
        # Connect first
        await self.transport.connect()
        
        message = {"test": "message"}
        
        # This should not raise an exception (placeholder implementation)
        await self.transport.send_message(message)
    
    async def test_receive_message_connected(self):
        """Test receiving message when connected."""
        # Connect first
        await self.transport.connect()
        
        # This should return a placeholder message
        message = await self.transport.receive_message()
        
        self.assertIsInstance(message, dict)
        self.assertEqual(message.get("jsonrpc"), "2.0")
    
    async def test_disconnect(self):
        """Test transport disconnection."""
        # Connect first
        await self.transport.connect()
        self.assertTrue(self.transport.is_connected())
        
        # Test disconnection
        await self.transport.disconnect()
        
        # Verify state cleanup
        self.assertFalse(self.transport.is_connected())
        self.assertIsNone(self.transport._session)


class TestTransportIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for transport functionality."""
    
    async def test_message_roundtrip_simulation(self):
        """Test simulated message roundtrip for both transports."""
        transports = [
            StdioTransport(),
            StreamingTransport()
        ]
        
        for transport in transports:
            with self.subTest(transport=transport.__class__.__name__):
                # For stdio, we'll skip the actual connection due to complexity
                if isinstance(transport, StreamingTransport):
                    await transport.connect()
                    
                    # Test message handling
                    test_message = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "test",
                        "params": {"key": "value"}
                    }
                    
                    # Send message (placeholder implementation)
                    await transport.send_message(test_message)
                    
                    # Receive message (placeholder implementation)
                    response = await transport.receive_message()
                    self.assertIsInstance(response, dict)
                    
                    await transport.disconnect()


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests
    unittest.main()