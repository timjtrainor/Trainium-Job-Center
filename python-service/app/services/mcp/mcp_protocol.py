"""MCP Protocol Handler.

This module implements the MCP protocol lifecycle and message exchange,
handling initialization handshake, capability negotiation, and session management.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import time

from .mcp_transport import MCPTransport
from .mcp_models import (
    JsonRpcRequest, JsonRpcResponse, InitializeRequest, InitializeResponse,
    create_error_response, create_success_response, JsonRpcErrorCodes
)
from .mcp_exceptions import (
    HandshakeError, ProtocolError, TimeoutError, MCPError,
    handshake_failed, protocol_violation, operation_timeout
)

logger = logging.getLogger(__name__)


class MCPProtocol:
    """Handles MCP protocol lifecycle and message exchange."""
    
    def __init__(self, transport: MCPTransport, timeout: int = 30):
        """Initialize MCP protocol handler.
        
        Args:
            transport: Transport layer implementation for communication
            timeout: Default timeout in seconds for protocol operations
        """
        self.transport = transport
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self.server_capabilities: Dict[str, Any] = {}
        self.is_initialized = False
        self._next_request_id = 1
        
    def _get_next_request_id(self) -> int:
        """Get next request ID for message exchange."""
        request_id = self._next_request_id
        self._next_request_id += 1
        return request_id
        
    async def initialize(self) -> Dict[str, Any]:
        """Perform MCP initialization handshake.
        
        Returns:
            Server capabilities and information from initialization response
            
        Raises:
            HandshakeError: If initialization fails
            TimeoutError: If initialization times out
            ProtocolError: If protocol violations occur
        """
        if self.is_initialized:
            logger.warning("Protocol already initialized, skipping")
            return self.server_capabilities
            
        logger.info("Starting MCP initialization handshake")
        
        try:
            # Create initialize request
            init_request = InitializeRequest()
            request_id = self._get_next_request_id()
            json_request = init_request.to_jsonrpc_request(request_id)
            
            logger.debug(f"Sending initialize request: {json_request.to_dict()}")
            
            # Send request directly (don't use send_request to avoid ID conflicts)
            await asyncio.wait_for(
                self.transport.send_message(json_request.to_dict()),
                timeout=self.timeout
            )
            
            # Receive response
            response_data = await asyncio.wait_for(
                self.transport.receive_message(),
                timeout=self.timeout
            )
            
            logger.debug(f"Received initialize response: {response_data}")
            
            # Parse response
            response = JsonRpcResponse.from_dict(response_data)
            
            # Validate response ID matches request
            if response.id != request_id:
                raise protocol_violation(
                    "initialize", 
                    f"Response ID {response.id} does not match request ID {request_id}"
                )
            
            # Handle error responses
            if response.error:
                error_msg = f"Server error: {response.error.message} (code: {response.error.code})"
                if response.error.data:
                    error_msg += f" - {response.error.data}"
                raise handshake_failed(error_msg)
            
            # Get result data
            result_data = response.result or {}
            
            
            # Parse and validate response
            if "protocolVersion" not in result_data:
                raise handshake_failed("Missing protocolVersion in server response")
                
            if "capabilities" not in result_data:
                raise handshake_failed("Missing capabilities in server response")
                
            if "serverInfo" not in result_data:
                raise handshake_failed("Missing serverInfo in server response")
                
            # Store server capabilities and info
            init_response = InitializeResponse.from_dict(result_data)
            self.server_capabilities = init_response.capabilities.to_dict()
            
            # Mark as initialized
            self.is_initialized = True
            
            logger.info(f"MCP initialization successful")
            logger.info(f"Server: {init_response.serverInfo}")
            logger.info(f"Protocol version: {init_response.protocolVersion}")
            logger.debug(f"Server capabilities: {self.server_capabilities}")
            
            return {
                "protocolVersion": init_response.protocolVersion,
                "capabilities": self.server_capabilities,
                "serverInfo": init_response.serverInfo
            }
            
        except asyncio.TimeoutError:
            raise operation_timeout("initialize", self.timeout)
        except HandshakeError:
            raise
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise handshake_failed(f"Unexpected error during initialization: {e}")
            
    async def send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Send JSON-RPC request and await response.
        
        Args:
            method: JSON-RPC method name
            params: Optional parameters for the request
            
        Returns:
            Response result data
            
        Raises:
            ProtocolError: If protocol violations occur
            TimeoutError: If request times out
            MCPError: For other MCP-related errors
        """
        request_id = self._get_next_request_id()
        
        # Create JSON-RPC request
        request = JsonRpcRequest(
            method=method,
            id=request_id,
            params=params
        )
        
        logger.debug(f"Sending request: {request.to_dict()}")
        
        try:
            # Send request through transport
            await asyncio.wait_for(
                self.transport.send_message(request.to_dict()),
                timeout=self.timeout
            )
            
            # Receive response
            response_data = await asyncio.wait_for(
                self.transport.receive_message(),
                timeout=self.timeout
            )
            
            logger.debug(f"Received response: {response_data}")
            
            # Parse response
            response = JsonRpcResponse.from_dict(response_data)
            
            # Validate response ID matches request
            if response.id != request_id:
                raise protocol_violation(
                    method, 
                    f"Response ID {response.id} does not match request ID {request_id}"
                )
            
            # Handle error responses
            if response.error:
                error_msg = f"Server error: {response.error.message} (code: {response.error.code})"
                if response.error.data:
                    error_msg += f" - {response.error.data}"
                raise ProtocolError(error_msg, method=method)
            
            # Return successful result
            return response.result or {}
            
        except asyncio.TimeoutError:
            raise operation_timeout(f"request {method}", self.timeout)
        except ProtocolError:
            raise
        except Exception as e:
            logger.error(f"Request {method} failed: {e}")
            raise ProtocolError(f"Request failed: {e}", method=method)
            
    async def shutdown(self) -> None:
        """Gracefully shutdown MCP session.
        
        Sends shutdown notification to server and cleans up session state.
        """
        if not self.is_initialized:
            logger.warning("Protocol not initialized, nothing to shutdown")
            return
            
        logger.info("Starting MCP session shutdown")
        
        try:
            # Send shutdown notification (no response expected)
            request = JsonRpcRequest(
                method="shutdown",
                id=self._get_next_request_id()
            )
            
            await asyncio.wait_for(
                self.transport.send_message(request.to_dict()),
                timeout=self.timeout
            )
            
            logger.info("Shutdown notification sent")
            
        except asyncio.TimeoutError:
            logger.warning("Shutdown notification timed out")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            # Clean up session state
            self.is_initialized = False
            self.session_id = None
            self.server_capabilities = {}
            logger.info("MCP session shutdown complete")
            
    def has_capability(self, capability: str) -> bool:
        """Check if server has a specific capability.
        
        Args:
            capability: Capability name to check (e.g., 'tools', 'resources')
            
        Returns:
            True if server has the capability
        """
        return capability in self.server_capabilities
        
    def get_capability_details(self, capability: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific server capability.
        
        Args:
            capability: Capability name
            
        Returns:
            Capability details or None if not available
        """
        return self.server_capabilities.get(capability)