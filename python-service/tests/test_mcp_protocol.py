"""Tests for MCP Protocol Handler.

Test suite for MCP protocol initialization, capability negotiation,
session management, and error handling.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Import MCP modules
from app.services.mcp.mcp_protocol import MCPProtocol
from app.services.mcp.mcp_session import MCPSession, create_mcp_session
from app.services.mcp.mcp_transport import MCPTransport
from app.services.mcp.mcp_models import (
    JsonRpcRequest, JsonRpcResponse, InitializeRequest, InitializeResponse,
    ServerCapabilities, JsonRpcError, JsonRpcErrorCodes
)
from app.services.mcp.mcp_exceptions import (
    HandshakeError, ProtocolError, TimeoutError, ConnectionError
)


class MockTransport(MCPTransport):
    """Mock transport for testing."""
    
    def __init__(self):
        super().__init__()
        self.sent_messages = []
        self.response_queue = []
        self.should_fail_connect = False
        self.should_timeout = False
        
    async def connect(self):
        if self.should_fail_connect:
            raise Exception("Mock connection failure")
        self._connected = True
        
    async def disconnect(self):
        self._connected = False
        
    async def send_message(self, message: Dict[str, Any]):
        if self.should_timeout:
            await asyncio.sleep(100)  # Simulate timeout
        self.sent_messages.append(message)
        
    async def receive_message(self) -> Dict[str, Any]:
        if self.should_timeout:
            await asyncio.sleep(100)  # Simulate timeout
        if not self.response_queue:
            raise Exception("No responses queued")
        return self.response_queue.pop(0)
        
    def queue_response(self, response: Dict[str, Any]):
        """Queue a response for the next receive_message call."""
        self.response_queue.append(response)


@pytest.fixture
def mock_transport():
    """Create mock transport for testing."""
    return MockTransport()


@pytest.fixture
def protocol(mock_transport):
    """Create MCP protocol instance with mock transport."""
    return MCPProtocol(mock_transport, timeout=1)  # Short timeout for tests


class TestMCPProtocol:
    """Test cases for MCP protocol handler."""
    
    @pytest.mark.asyncio
    async def test_mcp_initialize(self, protocol, mock_transport):
        """Test successful MCP initialization."""
        # Queue successful initialize response
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True}
                },
                "serverInfo": {
                    "name": "test-server",
                    "version": "1.0.0"
                }
            }
        }
        mock_transport.queue_response(init_response)
        
        # Test initialization
        result = await protocol.initialize()
        
        # Verify protocol state
        assert protocol.is_initialized is True
        assert result["protocolVersion"] == "2025-03-26"
        assert "tools" in result["capabilities"]
        assert result["serverInfo"]["name"] == "test-server"
        
        # Verify request was sent
        assert len(mock_transport.sent_messages) == 1
        sent_msg = mock_transport.sent_messages[0]
        assert sent_msg["method"] == "initialize"
        assert sent_msg["jsonrpc"] == "2.0"
        
    @pytest.mark.asyncio
    async def test_initialize_missing_protocol_version(self, protocol, mock_transport):
        """Test initialization failure with missing protocol version."""
        # Queue response missing protocolVersion
        bad_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "capabilities": {},
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(bad_response)
        
        # Test initialization should fail
        with pytest.raises(HandshakeError) as excinfo:
            await protocol.initialize()
            
        assert "Missing protocolVersion" in str(excinfo.value)
        assert protocol.is_initialized is False
        
    @pytest.mark.asyncio
    async def test_initialize_missing_capabilities(self, protocol, mock_transport):
        """Test initialization failure with missing capabilities."""
        # Queue response missing capabilities
        bad_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(bad_response)
        
        # Test initialization should fail
        with pytest.raises(HandshakeError) as excinfo:
            await protocol.initialize()
            
        assert "Missing capabilities" in str(excinfo.value)
        assert protocol.is_initialized is False
        
    @pytest.mark.asyncio
    async def test_capability_negotiation(self, protocol, mock_transport):
        """Test server capability parsing."""
        # Queue response with detailed capabilities
        capabilities = {
            "tools": {
                "listChanged": True,
                "subscribe": False
            },
            "resources": {
                "listChanged": True,
                "subscribe": True
            },
            "prompts": {
                "listChanged": False
            }
        }
        
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": capabilities,
                "serverInfo": {"name": "test-server", "version": "1.0.0"}
            }
        }
        mock_transport.queue_response(init_response)
        
        # Initialize and test capabilities
        await protocol.initialize()
        
        assert protocol.has_capability("tools")
        assert protocol.has_capability("resources")
        assert protocol.has_capability("prompts")
        assert not protocol.has_capability("nonexistent")
        
        # Test capability details
        tools_details = protocol.get_capability_details("tools")
        assert tools_details["listChanged"] is True
        assert tools_details["subscribe"] is False
        
        resources_details = protocol.get_capability_details("resources")
        assert resources_details["subscribe"] is True
        
    @pytest.mark.asyncio
    async def test_send_request_success(self, protocol, mock_transport):
        """Test successful request/response cycle."""
        # Initialize first
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26", 
                "capabilities": {},
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(init_response)
        await protocol.initialize()
        
        # Queue response for test request
        test_response = {
            "jsonrpc": "2.0", 
            "id": 2,
            "result": {
                "tools": [
                    {"name": "test_tool", "description": "A test tool"}
                ]
            }
        }
        mock_transport.queue_response(test_response)
        
        # Send test request
        result = await protocol.send_request("tools/list")
        
        # Verify result
        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "test_tool"
        
        # Verify request was sent correctly
        assert len(mock_transport.sent_messages) == 2  # init + test request
        test_request = mock_transport.sent_messages[1]
        assert test_request["method"] == "tools/list"
        assert test_request["id"] == 2
        
    @pytest.mark.asyncio
    async def test_send_request_with_params(self, protocol, mock_transport):
        """Test request with parameters."""
        # Initialize first
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(init_response)
        await protocol.initialize()
        
        # Queue response
        response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {"status": "success"}
        }
        mock_transport.queue_response(response)
        
        # Send request with parameters
        params = {"name": "test_tool", "arguments": {"query": "test"}}
        result = await protocol.send_request("tools/call", params)
        
        assert result["status"] == "success"
        
        # Verify parameters were sent
        request = mock_transport.sent_messages[1]
        assert request["params"] == params
        
    @pytest.mark.asyncio
    async def test_send_request_error_response(self, protocol, mock_transport):
        """Test handling of error responses."""
        # Initialize first
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(init_response)
        await protocol.initialize()
        
        # Queue error response
        error_response = {
            "jsonrpc": "2.0",
            "id": 2,
            "error": {
                "code": -32601,
                "message": "Method not found",
                "data": {"method": "unknown/method"}
            }
        }
        mock_transport.queue_response(error_response)
        
        # Send request should raise ProtocolError
        with pytest.raises(ProtocolError) as excinfo:
            await protocol.send_request("unknown/method")
            
        assert "Method not found" in str(excinfo.value)
        assert excinfo.value.method == "unknown/method"
        
    @pytest.mark.asyncio
    async def test_request_id_mismatch(self, protocol, mock_transport):
        """Test protocol error for mismatched request/response IDs."""
        # Initialize first
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(init_response)
        await protocol.initialize()
        
        # Queue response with wrong ID
        bad_response = {
            "jsonrpc": "2.0",
            "id": 999,  # Wrong ID
            "result": {"status": "ok"}
        }
        mock_transport.queue_response(bad_response)
        
        # Should raise ProtocolError
        with pytest.raises(ProtocolError) as excinfo:
            await protocol.send_request("test/method")
            
        assert "Response ID" in str(excinfo.value)
        assert "does not match request ID" in str(excinfo.value)
        
    @pytest.mark.asyncio
    async def test_protocol_timeout(self, protocol, mock_transport):
        """Test timeout handling."""
        mock_transport.should_timeout = True
        
        # Initialization should timeout
        with pytest.raises(TimeoutError) as excinfo:
            await protocol.initialize()
            
        assert "initialize" in str(excinfo.value)
        assert excinfo.value.timeout_seconds == 1
        
    @pytest.mark.asyncio
    async def test_shutdown(self, protocol, mock_transport):
        """Test graceful shutdown."""
        # Initialize first
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(init_response)
        await protocol.initialize()
        
        # Test shutdown
        await protocol.shutdown()
        
        # Verify shutdown message was sent
        assert len(mock_transport.sent_messages) == 2  # init + shutdown
        shutdown_msg = mock_transport.sent_messages[1]
        assert shutdown_msg["method"] == "shutdown"
        
        # Verify protocol state
        assert protocol.is_initialized is False
        assert protocol.session_id is None
        assert protocol.server_capabilities == {}


class TestMCPSession:
    """Test cases for MCP session management."""
    
    @pytest.mark.asyncio
    async def test_session_context_manager(self, mock_transport):
        """Test session lifecycle management."""
        # Queue successful initialize response
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "test-server", "version": "1.0.0"}
            }
        }
        mock_transport.queue_response(init_response)
        
        protocol = MCPProtocol(mock_transport, timeout=1)
        session = MCPSession(protocol)
        
        # Test context manager
        async with session as active_session:
            assert active_session.is_active is True
            assert active_session.protocol.is_initialized is True
            assert mock_transport.is_connected() is True
            
        # After context exit
        assert session.is_active is False
        assert mock_transport.is_connected() is False
        
    @pytest.mark.asyncio
    async def test_session_connection_failure(self, mock_transport):
        """Test session handling of connection failures."""
        mock_transport.should_fail_connect = True
        
        protocol = MCPProtocol(mock_transport, timeout=1)
        session = MCPSession(protocol)
        
        # Context manager should raise ConnectionError
        with pytest.raises(ConnectionError):
            async with session:
                pass
                
        assert session.is_active is False
        
    @pytest.mark.asyncio
    async def test_session_request_forwarding(self, mock_transport):
        """Test session request forwarding to protocol."""
        # Setup successful session
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(init_response)
        
        # Queue response for test request
        test_response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {"data": "test"}
        }
        mock_transport.queue_response(test_response)
        
        protocol = MCPProtocol(mock_transport, timeout=1)
        session = MCPSession(protocol)
        
        async with session as active_session:
            result = await active_session.send_request("test/method")
            assert result["data"] == "test"
            
    @pytest.mark.asyncio
    async def test_session_capability_check(self, mock_transport):
        """Test session capability checking."""
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(init_response)
        
        protocol = MCPProtocol(mock_transport, timeout=1)
        session = MCPSession(protocol)
        
        async with session as active_session:
            assert active_session.has_capability("tools") is True
            assert active_session.has_capability("resources") is False
            
    @pytest.mark.asyncio 
    async def test_create_mcp_session_convenience(self, mock_transport):
        """Test convenience function for creating sessions."""
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(init_response)
        
        async with create_mcp_session(mock_transport) as session:
            assert session.is_active is True
            assert isinstance(session, MCPSession)


class TestProtocolErrorHandling:
    """Test cases for protocol error scenarios."""
    
    @pytest.mark.asyncio
    async def test_double_initialization(self, protocol, mock_transport):
        """Test that double initialization is handled gracefully."""
        # First initialization
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": "test"}
            }
        }
        mock_transport.queue_response(init_response)
        await protocol.initialize()
        
        # Second initialization should not send another request
        result = await protocol.initialize()
        assert len(mock_transport.sent_messages) == 1  # Only one init message
        
    @pytest.mark.asyncio
    async def test_request_before_initialization(self, protocol, mock_transport):
        """Test sending requests before initialization."""
        # This should work as send_request doesn't check initialization state
        # The protocol allows sending requests after transport connection
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"status": "ok"}
        }
        mock_transport.queue_response(response)
        
        result = await protocol.send_request("test/method")
        assert result["status"] == "ok"
        
    @pytest.mark.asyncio
    async def test_shutdown_before_initialization(self, protocol, mock_transport):
        """Test shutdown before initialization."""
        # Should handle gracefully
        await protocol.shutdown()
        
        # No messages should be sent
        assert len(mock_transport.sent_messages) == 0