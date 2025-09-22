"""MCP Transport Layer Abstraction.

This module provides the foundational transport abstraction and implementations
for the Model Context Protocol (MCP) communication layer.
"""

import asyncio
import json
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MCPTransport(ABC):
    """Abstract base class for MCP transport implementations."""
    
    def __init__(self):
        self._connected = False
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish transport connection."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Close transport connection."""
        pass
        
    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send JSON-RPC message."""
        pass
        
    @abstractmethod
    async def receive_message(self) -> Dict[str, Any]:
        """Receive JSON-RPC message."""
        pass
        
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected


class StdioTransport(MCPTransport):
    """Transport for stdio communication with MCP Gateway.
    
    This transport handles stdin/stdout JSON-RPC communication without
    external dependencies, using asyncio streams for non-blocking I/O.
    """
    
    def __init__(self):
        super().__init__()
        self._stdin_reader: Optional[asyncio.StreamReader] = None
        self._stdout_writer: Optional[asyncio.StreamWriter] = None
        
    async def connect(self) -> None:
        """Establish stdio transport connection."""
        try:
            # Create asyncio streams for stdin/stdout
            loop = asyncio.get_event_loop()
            
            # Create stdin reader
            self._stdin_reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self._stdin_reader)
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)
            
            # Create stdout writer
            transport, protocol = await loop.connect_write_pipe(
                asyncio.streams.FlowControlMixin, sys.stdout
            )
            self._stdout_writer = asyncio.StreamWriter(transport, protocol, None, loop)
            
            self._connected = True
            logger.info("StdioTransport connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect stdio transport: {e}")
            raise Exception(f"Failed to establish stdio connection: {e}")
    
    async def disconnect(self) -> None:
        """Close stdio transport connection."""
        try:
            if self._stdout_writer:
                self._stdout_writer.close()
                await self._stdout_writer.wait_closed()
            
            self._stdin_reader = None
            self._stdout_writer = None
            self._connected = False
            
            logger.info("StdioTransport disconnected successfully")
            
        except Exception as e:
            logger.error(f"Error during stdio disconnect: {e}")
            raise
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send JSON-RPC message via stdout."""
        if not self._connected or not self._stdout_writer:
            raise Exception("Transport not connected")
        
        try:
            # Serialize message to JSON
            json_message = json.dumps(message)
            
            # Write message with newline delimiter
            self._stdout_writer.write(f"{json_message}\n".encode('utf-8'))
            await self._stdout_writer.drain()
            
            logger.debug(f"Sent message: {json_message}")
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise IOError(f"Failed to send message: {e}")
    
    async def receive_message(self) -> Dict[str, Any]:
        """Receive JSON-RPC message from stdin."""
        if not self._connected or not self._stdin_reader:
            raise Exception("Transport not connected")
        
        try:
            # Read line from stdin
            line = await self._stdin_reader.readline()
            if not line:
                raise EOFError("EOF reached on stdin")
            
            # Decode and parse JSON
            json_str = line.decode('utf-8').strip()
            if not json_str:
                raise ValueError("Empty message received")
            
            message = json.loads(json_str)
            logger.debug(f"Received message: {json_str}")
            
            return message
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            raise ValueError(f"Invalid JSON message: {e}")
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            raise IOError(f"Failed to receive message: {e}")


class StreamingTransport(MCPTransport):
    """Transport for HTTP streaming communication with MCP Gateway.
    
    This is a basic implementation that can be extended with proper HTTP
    streaming capabilities when aiohttp is available.
    """
    
    def __init__(self, gateway_url: str = "http://mcp-gateway:8811"):
        super().__init__()
        self.gateway_url = gateway_url
        self._session = None
        
    async def connect(self) -> None:
        """Establish HTTP streaming transport connection."""
        try:
            # Basic connection placeholder - would use aiohttp in full implementation
            logger.info(f"StreamingTransport connecting to {self.gateway_url}")
            
            # For now, just mark as connected - real implementation would
            # establish HTTP connection and verify gateway availability
            self._connected = True
            logger.info("StreamingTransport connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect streaming transport: {e}")
            raise Exception(f"Failed to establish streaming connection: {e}")
    
    async def disconnect(self) -> None:
        """Close HTTP streaming transport connection."""
        try:
            if self._session:
                # Would close aiohttp session here
                self._session = None
            
            self._connected = False
            logger.info("StreamingTransport disconnected successfully")
            
        except Exception as e:
            logger.error(f"Error during streaming disconnect: {e}")
            raise
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send JSON-RPC message via HTTP streaming."""
        if not self._connected:
            raise Exception("Transport not connected")
        
        try:
            # Placeholder implementation - would use aiohttp to POST message
            json_message = json.dumps(message)
            logger.debug(f"Would send via HTTP: {json_message}")
            
            # Real implementation would POST to gateway_url/jsonrpc
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise IOError(f"Failed to send message: {e}")
    
    async def receive_message(self) -> Dict[str, Any]:
        """Receive JSON-RPC message from HTTP streaming."""
        if not self._connected:
            raise Exception("Transport not connected")
        
        try:
            # Placeholder implementation - would use aiohttp streaming response
            logger.debug("Would receive via HTTP streaming")
            
            # Real implementation would read from streaming HTTP response
            # For now, return a placeholder message
            return {"jsonrpc": "2.0", "id": 1, "result": {"status": "placeholder"}}
            
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            raise IOError(f"Failed to receive message: {e}")