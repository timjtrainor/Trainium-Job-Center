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

import httpx

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
        self.gateway_url = gateway_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
        self._response_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._send_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Establish HTTP streaming transport connection."""
        try:
            if self._connected:
                logger.debug("StreamingTransport already connected")
                return

            logger.info(f"StreamingTransport connecting to {self.gateway_url}")

            self._client = httpx.AsyncClient(base_url=self.gateway_url)
            # Reset response queue for a fresh session
            self._response_queue = asyncio.Queue()

            self._connected = True
            logger.info("StreamingTransport connected successfully")

        except Exception as e:
            logger.error(f"Failed to connect streaming transport: {e}")
            raise Exception(f"Failed to establish streaming connection: {e}")
    
    async def disconnect(self) -> None:
        """Close HTTP streaming transport connection."""
        try:
            if self._client:
                await self._client.aclose()

            self._client = None
            self._connected = False

            # Drain any pending responses to avoid leaking state across sessions
            while not self._response_queue.empty():
                try:
                    self._response_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

            logger.info("StreamingTransport disconnected successfully")

        except Exception as e:
            logger.error(f"Error during streaming disconnect: {e}")
            raise

    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send JSON-RPC message via HTTP streaming."""
        if not self._connected or self._client is None:
            raise Exception("Transport not connected")

        method = message.get("method")
        if not method:
            raise ValueError("JSON-RPC message missing 'method'")

        endpoint = self._resolve_endpoint(method)

        # Notifications like shutdown do not expect responses; skip HTTP roundtrip
        if endpoint is None:
            if method == "shutdown":
                logger.debug("Skipping HTTP call for '%s' notification", method)
                return

            logger.warning("No HTTP endpoint mapped for method '%s'", method)
            await self._response_queue.put(
                self._build_error_response(
                    message,
                    -32601,
                    f"Method not supported: {method}",
                )
            )
            return

        async with self._send_lock:
            try:
                logger.debug("Sending JSON-RPC '%s' to %s", method, endpoint)
                response = await self._client.post(endpoint, json=message)
            except httpx.RequestError as exc:
                logger.error("HTTP request error for %s: %s", endpoint, exc)
                await self._response_queue.put(
                    self._build_error_response(
                        message,
                        -32000,
                        f"HTTP request failed: {exc}"
                    )
                )
                return

            try:
                payload = response.json()
            except ValueError as exc:
                logger.error("Invalid JSON from %s: %s", endpoint, exc)
                payload = self._build_error_response(
                    message,
                    -32700,
                    f"Invalid JSON response: {exc}"
                )

            if response.status_code >= 400:
                logger.warning(
                    "Gateway returned HTTP %s for method '%s'", response.status_code, method
                )

            await self._response_queue.put(payload)

    async def receive_message(self) -> Dict[str, Any]:
        """Receive JSON-RPC message from HTTP streaming."""
        if not self._connected:
            raise Exception("Transport not connected")

        try:
            response = await self._response_queue.get()
            logger.debug("Delivering cached response: %s", response)
            return response
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            raise IOError(f"Failed to receive message: {e}")

    def _resolve_endpoint(self, method: str) -> Optional[str]:
        """Map JSON-RPC method names to MCP gateway endpoints."""
        mapping = {
            "initialize": "/mcp/initialize",
            "tools/list": "/mcp/tools/list",
            "tools/call": "/mcp/tools/call",
        }
        return mapping.get(method)

    def _build_error_response(
        self,
        message: Dict[str, Any],
        code: int,
        error_message: str,
    ) -> Dict[str, Any]:
        """Create a JSON-RPC error response payload."""
        return {
            "jsonrpc": message.get("jsonrpc", "2.0"),
            "id": message.get("id"),
            "error": {
                "code": code,
                "message": error_message,
            },
        }