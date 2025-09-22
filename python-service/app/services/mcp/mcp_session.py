"""MCP Session Management.

This module provides session lifecycle management with async context manager
support for MCP protocol operations.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncContextManager
from contextlib import asynccontextmanager

from .mcp_protocol import MCPProtocol
from .mcp_transport import MCPTransport
from .mcp_exceptions import ConnectionError, MCPError, connection_failed

logger = logging.getLogger(__name__)


class MCPSession:
    """Manages MCP session lifecycle with context manager support.
    
    This class provides a high-level interface for managing MCP sessions,
    handling connection, initialization, and cleanup automatically.
    """
    
    def __init__(self, protocol: MCPProtocol):
        """Initialize MCP session manager.
        
        Args:
            protocol: MCP protocol handler instance
        """
        self.protocol = protocol
        self._session_data: Dict[str, Any] = {}
        self._is_active = False
        
    async def __aenter__(self) -> 'MCPSession':
        """Async context manager entry.
        
        Establishes transport connection and performs MCP initialization.
        
        Returns:
            Self for use in context
            
        Raises:
            ConnectionError: If transport connection fails
            HandshakeError: If MCP initialization fails
        """
        logger.info("Starting MCP session")
        
        try:
            # Connect transport
            await self.protocol.transport.connect()
            logger.debug("Transport connected successfully")
            
            # Initialize MCP protocol
            init_result = await self.protocol.initialize()
            self._session_data.update(init_result)
            
            self._is_active = True
            logger.info("MCP session established successfully")
            
            return self
            
        except Exception as e:
            logger.error(f"Failed to establish MCP session: {e}")
            
            # Attempt cleanup on failure
            try:
                await self._cleanup()
            except Exception as cleanup_error:
                logger.error(f"Error during session cleanup: {cleanup_error}")
                
            # Re-raise original error
            if isinstance(e, (ConnectionError, MCPError)):
                raise
            else:
                raise connection_failed("localhost", e)
                
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit.
        
        Performs graceful shutdown and cleanup of MCP session.
        """
        logger.info("Ending MCP session")
        
        try:
            await self._cleanup()
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
        finally:
            self._is_active = False
            logger.info("MCP session ended")
            
    async def _cleanup(self) -> None:
        """Internal cleanup method."""
        if self.protocol.is_initialized:
            await self.protocol.shutdown()
            
        if self.protocol.transport.is_connected():
            await self.protocol.transport.disconnect()
            
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self._is_active and self.protocol.is_initialized
        
    @property
    def server_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities from the session."""
        return self.protocol.server_capabilities
        
    @property
    def session_info(self) -> Dict[str, Any]:
        """Get session information."""
        return {
            "active": self.is_active,
            "initialized": self.protocol.is_initialized,
            "connected": self.protocol.transport.is_connected(),
            "capabilities": self.server_capabilities,
            "session_data": self._session_data.copy()
        }
        
    async def send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Send request through the session.
        
        Args:
            method: JSON-RPC method name
            params: Optional request parameters
            
        Returns:
            Response result data
            
        Raises:
            MCPError: If session is not active or request fails
        """
        if not self.is_active:
            raise MCPError("Session is not active")
            
        return await self.protocol.send_request(method, params)
        
    def has_capability(self, capability: str) -> bool:
        """Check if server has a specific capability.
        
        Args:
            capability: Capability name to check
            
        Returns:
            True if server has the capability
        """
        return self.protocol.has_capability(capability)


@asynccontextmanager
async def create_mcp_session(transport: MCPTransport, timeout: int = 30) -> AsyncContextManager[MCPSession]:
    """Create and manage an MCP session with automatic cleanup.
    
    This is a convenience function that creates a complete MCP session
    with protocol handler and session management.
    
    Args:
        transport: Transport implementation to use
        timeout: Timeout for protocol operations
        
    Yields:
        Active MCP session
        
    Example:
        async with create_mcp_session(transport) as session:
            result = await session.send_request("tools/list")
    """
    from .mcp_protocol import MCPProtocol
    
    protocol = MCPProtocol(transport, timeout)
    session = MCPSession(protocol)
    
    async with session as active_session:
        yield active_session


class MCPSessionPool:
    """Pool manager for multiple MCP sessions.
    
    This class can be used to manage multiple concurrent MCP sessions
    for different transports or connection endpoints.
    """
    
    def __init__(self, max_sessions: int = 10):
        """Initialize session pool.
        
        Args:
            max_sessions: Maximum number of concurrent sessions
        """
        self.max_sessions = max_sessions
        self._sessions: Dict[str, MCPSession] = {}
        self._session_lock = asyncio.Lock()
        
    async def get_session(self, session_id: str, transport: MCPTransport, timeout: int = 30) -> MCPSession:
        """Get or create a session from the pool.
        
        Args:
            session_id: Unique identifier for the session
            transport: Transport implementation
            timeout: Protocol timeout
            
        Returns:
            Active MCP session
            
        Raises:
            MCPError: If pool is full or session creation fails
        """
        async with self._session_lock:
            # Return existing session if available and active
            if session_id in self._sessions:
                session = self._sessions[session_id]
                if session.is_active:
                    return session
                else:
                    # Clean up inactive session
                    del self._sessions[session_id]
                    
            # Check pool capacity
            if len(self._sessions) >= self.max_sessions:
                raise MCPError(f"Session pool full (max: {self.max_sessions})")
                
            # Create new session
            protocol = MCPProtocol(transport, timeout)
            session = MCPSession(protocol)
            
            # Initialize session
            async with session:  # This will establish the connection
                self._sessions[session_id] = session
                return session
                
    async def close_session(self, session_id: str) -> None:
        """Close and remove a session from the pool.
        
        Args:
            session_id: Session identifier to close
        """
        async with self._session_lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                try:
                    await session._cleanup()
                except Exception as e:
                    logger.error(f"Error closing session {session_id}: {e}")
                finally:
                    del self._sessions[session_id]
                    
    async def close_all_sessions(self) -> None:
        """Close all sessions in the pool."""
        async with self._session_lock:
            session_ids = list(self._sessions.keys())
            
            for session_id in session_ids:
                try:
                    await self.close_session(session_id)
                except Exception as e:
                    logger.error(f"Error closing session {session_id}: {e}")
                    
            self._sessions.clear()
            
    @property
    def active_session_count(self) -> int:
        """Get count of active sessions."""
        return len([s for s in self._sessions.values() if s.is_active])
        
    @property
    def session_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all sessions in the pool."""
        return {
            session_id: session.session_info
            for session_id, session in self._sessions.items()
        }