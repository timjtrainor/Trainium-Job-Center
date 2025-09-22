"""Main MCP Gateway Adapter Class.

This module provides the main MCPGatewayAdapter class that coordinates between
transport, protocol, and tools components to provide a unified interface for
MCP operations.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
import time

from .mcp_transport import MCPTransport, StdioTransport, StreamingTransport
from .mcp_protocol import MCPProtocol
from .mcp_session import MCPSession
from .mcp_tools import MCPToolManager  
from .mcp_exceptions import MCPError, ConfigurationError
from .mcp_logging import configure_logging, get_mcp_logger, MCPLoggerAdapter

logger = logging.getLogger(__name__)


class MCPGatewayAdapter:
    """Main adapter for Docker MCP Gateway integration."""
    
    def __init__(
        self,
        transport: MCPTransport,
        timeout: int = 30,
        max_retries: int = 3,
        log_level: str = "INFO"
    ):
        """Initialize the MCP Gateway adapter.
        
        Args:
            transport: Transport implementation for communication
            timeout: Default timeout in seconds for operations
            max_retries: Maximum number of retry attempts  
            log_level: Logging level for the adapter
        """
        # Configure logging first
        configure_logging(log_level)
        self.logger = get_mcp_logger(
            "mcp.adapter", 
            transport_type=transport.__class__.__name__.lower().replace('transport', '')
        )
        
        self.transport = transport
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize core components
        self.protocol = MCPProtocol(transport, timeout)
        self.tool_manager = MCPToolManager(self.protocol)
        self.session: Optional[MCPSession] = None
        
        # Connection state
        self._connected = False
        self._connection_lock = asyncio.Lock()
        
        # Metrics
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0
        
        self.logger.info(
            "MCPGatewayAdapter initialized",
            extra={
                "timeout": timeout,
                "max_retries": max_retries,
                "transport_type": type(transport).__name__
            }
        )
        
    async def connect(self) -> None:
        """Establish connection and perform MCP handshake.
        
        Raises:
            ConnectionError: If connection establishment fails
            HandshakeError: If MCP handshake fails
            MCPError: For other connection-related errors
        """
        async with self._connection_lock:
            if self._connected:
                self.logger.warning("Already connected, skipping connection")
                return
                
            self.logger.info("Establishing MCP gateway connection")
            
            retry_count = 0
            last_error = None
            
            while retry_count <= self.max_retries:
                try:
                    # Create new session for this connection attempt
                    self.session = MCPSession(self.protocol)
                    
                    # Use session context manager to establish connection
                    await self.session.__aenter__()
                    
                    self._connected = True
                    
                    self.logger.info(
                        "MCP gateway connection established successfully",
                        extra={
                            "retry_count": retry_count,
                            "capabilities": list(self.session.server_capabilities.keys())
                        }
                    )
                    return
                    
                except Exception as e:
                    last_error = e
                    retry_count += 1
                    self._error_count += 1
                    
                    if retry_count <= self.max_retries:
                        wait_time = min(2 ** (retry_count - 1), 10)  # Exponential backoff, max 10s
                        self.logger.warning(
                            f"Connection attempt {retry_count} failed, retrying in {wait_time}s",
                            extra={
                                "error": str(e), 
                                "retry_count": retry_count,
                                "max_retries": self.max_retries
                            }
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        self.logger.error(
                            "All connection attempts failed",
                            extra={
                                "error": str(e),
                                "total_attempts": retry_count
                            }
                        )
            
            # If we get here, all retries failed
            if isinstance(last_error, MCPError):
                raise last_error
            else:
                raise MCPError(f"Failed to connect after {self.max_retries + 1} attempts: {last_error}")
                
    async def disconnect(self) -> None:
        """Gracefully close connection and cleanup resources.
        
        This method ensures proper cleanup of all resources and can be called
        multiple times safely.
        """
        async with self._connection_lock:
            if not self._connected:
                self.logger.debug("Not connected, skipping disconnect")
                return
                
            self.logger.info("Disconnecting from MCP gateway")
            
            try:
                # Cleanup session if it exists
                if self.session:
                    try:
                        await self.session.__aexit__(None, None, None)
                    except Exception as e:
                        self.logger.warning(f"Error during session cleanup: {e}")
                    finally:
                        self.session = None
                        
                # Clear tool manager cache
                self.tool_manager.clear_cache()
                
                self._connected = False
                self.logger.info("MCP gateway disconnection completed")
                
            except Exception as e:
                self._error_count += 1
                self.logger.error(f"Error during disconnect: {e}")
                raise MCPError(f"Disconnect failed: {e}")
                
    def is_connected(self) -> bool:
        """Check if gateway connection is active.
        
        Returns:
            True if connected and session is active
        """
        return (
            self._connected and 
            self.session is not None and 
            self.session.is_active
        )
        
    async def list_tools(self) -> Dict[str, Dict]:
        """Discover and return available tools with metadata.
        
        Returns:
            Dictionary mapping tool names to tool information
            
        Raises:
            MCPError: If not connected or tool discovery fails
        """
        if not self.is_connected():
            raise MCPError("Not connected to MCP gateway")
            
        self._request_count += 1
        
        try:
            self.logger.debug("Discovering available tools")
            tools = await self.tool_manager.discover_tools()
            
            self.logger.info(
                f"Successfully discovered {len(tools)} tools",
                extra={"tool_count": len(tools), "tool_names": list(tools.keys())}
            )
            
            return tools
            
        except Exception as e:
            self._error_count += 1
            self.logger.error(f"Tool discovery failed: {e}")
            raise MCPError(f"Failed to list tools: {e}")
            
    async def get_tool_info(self, tool_name: str) -> Dict:
        """Get detailed information about a specific tool.
        
        Args:
            tool_name: Name of the tool to get information for
            
        Returns:
            Tool information dictionary
            
        Raises:
            MCPError: If not connected or tool not found
        """
        if not self.is_connected():
            raise MCPError("Not connected to MCP gateway")
            
        self._request_count += 1
        
        try:
            self.logger.debug(f"Getting tool info for: {tool_name}")
            tool_info = await self.tool_manager.get_tool_info(tool_name)
            
            self.logger.debug(
                f"Retrieved tool info for {tool_name}",
                extra={"tool_name": tool_name, "has_schema": "inputSchema" in tool_info}
            )
            
            return tool_info
            
        except Exception as e:
            self._error_count += 1
            self.logger.error(f"Failed to get tool info for {tool_name}: {e}")
            raise MCPError(f"Failed to get tool info: {e}")
            
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return normalized results.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments dictionary
            
        Returns:
            Normalized tool execution result with metadata
            
        Raises:
            MCPError: If not connected or tool execution fails
        """
        if not self.is_connected():
            raise MCPError("Not connected to MCP gateway")
            
        self._request_count += 1
        
        try:
            self.logger.info(
                f"Executing tool: {tool_name}",
                extra={
                    "tool_name": tool_name,
                    "argument_keys": list(arguments.keys()) if arguments else []
                }
            )
            
            result = await self.tool_manager.execute_tool(tool_name, arguments)
            
            self.logger.info(
                f"Tool execution completed: {tool_name}",
                extra={
                    "tool_name": tool_name,
                    "success": result.get("success", False),
                    "execution_time": result.get("metadata", {}).get("execution_time")
                }
            )
            
            return result
            
        except Exception as e:
            self._error_count += 1
            self.logger.error(
                f"Tool execution failed: {tool_name}",
                extra={"tool_name": tool_name, "error": str(e)}
            )
            raise MCPError(f"Failed to execute tool: {e}")
            
    async def __aenter__(self):
        """Async context manager entry.
        
        Establishes connection automatically when entering context.
        
        Returns:
            Self for use in context
        """
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit.
        
        Ensures proper cleanup when exiting context.
        """
        await self.disconnect()
        
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection status and information.
        
        Returns:
            Dictionary with connection details
        """
        base_info = {
            "connected": self.is_connected(),
            "transport_type": type(self.transport).__name__,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
        
        if self.session:
            base_info.update({
                "session_active": self.session.is_active,
                "server_capabilities": list(self.session.server_capabilities.keys()),
                "protocol_initialized": self.session.protocol.is_initialized
            })
            
        return base_info
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get adapter performance and usage metrics.
        
        Returns:
            Dictionary with metrics data
        """
        uptime = time.time() - self._start_time
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "connected": self.is_connected(),
            "tool_cache_info": self.tool_manager.cache_info if self.tool_manager else None
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check.
        
        Returns:
            Health status dictionary
            
        Raises:
            MCPError: If health check fails
        """
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "connection": self.get_connection_info(),
            "metrics": self.get_metrics()
        }
        
        try:
            if self.is_connected():
                # Test basic connectivity by listing tools
                tools = await self.list_tools()
                health_data["tools_available"] = len(tools)
                health_data["status"] = "healthy"
            else:
                health_data["status"] = "disconnected"
                health_data["tools_available"] = 0
                
        except Exception as e:
            health_data["status"] = "unhealthy"
            health_data["error"] = str(e)
            self.logger.warning(f"Health check failed: {e}")
            
        return health_data
        
    def has_capability(self, capability: str) -> bool:
        """Check if the connected server has a specific capability.
        
        Args:
            capability: Capability name to check
            
        Returns:
            True if server has the capability (False if not connected)
        """
        if not self.is_connected() or not self.session:
            return False
            
        return self.session.has_capability(capability)
        
    async def validate_tool_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments without executing the tool.
        
        Args:
            tool_name: Name of the tool
            arguments: Arguments to validate
            
        Returns:
            True if arguments are valid
            
        Raises:
            MCPError: If not connected or validation fails
        """
        if not self.is_connected():
            raise MCPError("Not connected to MCP gateway")
            
        return await self.tool_manager.validate_tool_arguments(tool_name, arguments)


