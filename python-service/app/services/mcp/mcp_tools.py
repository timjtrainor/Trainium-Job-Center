"""MCP Tool Manager.

This module implements tool discovery and execution functionality for the
Model Context Protocol (MCP), providing high-level interfaces for working
with MCP tools.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from jsonschema import validate, ValidationError

from .mcp_protocol import MCPProtocol
from .mcp_models import JsonRpcRequest, ToolInfo, ToolListResponse, ToolCallRequest, ToolCallResponse
from .mcp_exceptions import ToolExecutionError, ProtocolError, TimeoutError, tool_execution_failed
from .mcp_results import ResultNormalizer

logger = logging.getLogger(__name__)


class MCPToolManager:
    """Manages tool discovery and execution."""
    
    def __init__(self, protocol: MCPProtocol, cache_ttl: int = 300):
        """Initialize tool manager.
        
        Args:
            protocol: MCP protocol handler instance
            cache_ttl: Tool cache TTL in seconds (default: 5 minutes)
        """
        self.protocol = protocol
        self.cache_ttl = cache_ttl
        self.tools_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamp: Optional[float] = None
        self._discovery_lock = asyncio.Lock()
        
    async def discover_tools(self) -> Dict[str, Dict[str, Any]]:
        """Discover available tools from the gateway.
        
        Returns:
            Dictionary mapping tool names to tool information
            
        Raises:
            ProtocolError: If tools/list request fails
            TimeoutError: If discovery times out
        """
        # Check cache first
        if self._is_cache_valid():
            logger.debug(f"Returning cached tools: {len(self.tools_cache)} tools")
            return self.tools_cache.copy()
        
        # Use lock to prevent concurrent discovery requests
        async with self._discovery_lock:
            # Double-check cache after acquiring lock
            if self._is_cache_valid():
                return self.tools_cache.copy()
            
            logger.info("Discovering tools from MCP gateway")
            
            try:
                # Send tools/list request
                result = await self.protocol.send_request("tools/list")
                
                # Parse response
                tools_response = ToolListResponse.from_dict(result)
                
                # Build tools cache
                new_cache = {}
                for tool in tools_response.tools:
                    tool_dict = tool.to_dict()
                    new_cache[tool.name] = tool_dict
                
                # Update cache
                self.tools_cache = new_cache
                self.cache_timestamp = time.time()
                
                logger.info(f"Successfully discovered {len(self.tools_cache)} tools")
                logger.debug(f"Tools: {list(self.tools_cache.keys())}")
                
                return self.tools_cache.copy()
                
            except Exception as e:
                logger.error(f"Tool discovery failed: {e}")
                if isinstance(e, (ProtocolError, TimeoutError)):
                    raise
                else:
                    raise ProtocolError(f"Tool discovery failed: {e}", method="tools/list")
    
    async def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific tool.
        
        Args:
            tool_name: Name of the tool to get info for
            
        Returns:
            Tool information dictionary
            
        Raises:
            ToolExecutionError: If tool is not found
        """
        # Ensure tools are discovered
        tools = await self.discover_tools()
        
        if tool_name not in tools:
            available_tools = list(tools.keys())
            raise tool_execution_failed(
                tool_name,
                f"Tool not found. Available tools: {available_tools}",
                arguments=None
            )
        
        tool_info = tools[tool_name].copy()
        logger.debug(f"Retrieved info for tool '{tool_name}': {tool_info}")
        
        return tool_info
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return normalized results.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments dictionary
            
        Returns:
            Normalized tool execution result
            
        Raises:
            ToolExecutionError: If tool execution fails
            ProtocolError: If communication fails
        """
        logger.info(f"Executing tool '{tool_name}' with arguments: {arguments}")
        
        try:
            # Get tool info for validation
            tool_info = await self.get_tool_info(tool_name)
            
            # Validate arguments against tool schema if available
            input_schema = tool_info.get("inputSchema")
            if input_schema:
                try:
                    validate(instance=arguments, schema=input_schema)
                    logger.debug(f"Arguments validated successfully for tool '{tool_name}'")
                except ValidationError as e:
                    raise tool_execution_failed(
                        tool_name,
                        f"Invalid arguments: {e.message}",
                        arguments=arguments
                    )
            
            # Create tool call request
            tool_request = ToolCallRequest(name=tool_name, arguments=arguments)
            
            # Execute tool via protocol
            start_time = time.time()
            result = await self.protocol.send_request("tools/call", tool_request.to_dict())
            execution_time = time.time() - start_time
            
            # Parse response
            tool_response = ToolCallResponse.from_dict(result)
            
            # Check for tool-level errors
            if tool_response.has_error():
                error_msg = tool_response.get_error_message() or "Tool execution failed"
                raise tool_execution_failed(tool_name, error_msg, arguments=arguments)
            
            # Normalize result
            normalized_result = ResultNormalizer.normalize_result(result)
            
            # Add execution metadata
            normalized_result["metadata"]["execution_time"] = execution_time
            normalized_result["metadata"]["tool_name"] = tool_name
            normalized_result["metadata"]["arguments"] = arguments
            
            if normalized_result["success"]:
                logger.info(f"Tool '{tool_name}' executed successfully in {execution_time:.2f}s")
            else:
                logger.warning(f"Tool '{tool_name}' execution completed with errors in {execution_time:.2f}s")
            
            return normalized_result
            
        except ToolExecutionError:
            # Re-raise tool execution errors as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing tool '{tool_name}': {e}")
            if isinstance(e, (ProtocolError, TimeoutError)):
                raise
            else:
                raise tool_execution_failed(tool_name, f"Unexpected error: {e}", arguments=arguments)
    
    def list_tool_names(self) -> List[str]:
        """Return list of available tool names.
        
        Returns:
            List of tool names from cache (empty if not discovered yet)
        """
        if not self._is_cache_valid():
            logger.warning("Tools not discovered yet, returning empty list")
            return []
        
        tool_names = list(self.tools_cache.keys())
        logger.debug(f"Available tools: {tool_names}")
        return tool_names
    
    def get_cached_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get cached tools without triggering discovery.
        
        Returns:
            Cached tools dictionary (empty if cache invalid)
        """
        if not self._is_cache_valid():
            return {}
        return self.tools_cache.copy()
    
    def clear_cache(self) -> None:
        """Clear the tools cache to force rediscovery."""
        logger.info("Clearing tools cache")
        self.tools_cache.clear()
        self.cache_timestamp = None
    
    def _is_cache_valid(self) -> bool:
        """Check if the tools cache is still valid."""
        if not self.tools_cache or self.cache_timestamp is None:
            return False
        
        age = time.time() - self.cache_timestamp
        is_valid = age < self.cache_ttl
        
        if not is_valid:
            logger.debug(f"Cache expired (age: {age:.1f}s, TTL: {self.cache_ttl}s)")
        
        return is_valid
    
    @property
    def cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        if self.cache_timestamp is None:
            return {
                "cached": False,
                "tool_count": 0,
                "age_seconds": None,
                "ttl_seconds": self.cache_ttl,
                "valid": False
            }
        
        age = time.time() - self.cache_timestamp
        return {
            "cached": bool(self.tools_cache),
            "tool_count": len(self.tools_cache),
            "age_seconds": age,
            "ttl_seconds": self.cache_ttl,
            "valid": self._is_cache_valid()
        }
    
    async def validate_tool_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments without executing the tool.
        
        Args:
            tool_name: Name of the tool
            arguments: Arguments to validate
            
        Returns:
            True if arguments are valid
            
        Raises:
            ToolExecutionError: If tool not found or validation fails
        """
        tool_info = await self.get_tool_info(tool_name)
        
        input_schema = tool_info.get("inputSchema")
        if not input_schema:
            logger.debug(f"No input schema for tool '{tool_name}', validation skipped")
            return True
        
        try:
            validate(instance=arguments, schema=input_schema)
            logger.debug(f"Arguments valid for tool '{tool_name}'")
            return True
        except ValidationError as e:
            raise tool_execution_failed(
                tool_name,
                f"Invalid arguments: {e.message}",
                arguments=arguments
            )
    
    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the input schema for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Input schema dictionary or None if not available
            
        Raises:
            ToolExecutionError: If tool not found
        """
        tool_info = await self.get_tool_info(tool_name)
        schema = tool_info.get("inputSchema")
        
        if schema:
            logger.debug(f"Retrieved schema for tool '{tool_name}': {json.dumps(schema, indent=2)}")
        else:
            logger.debug(f"No schema available for tool '{tool_name}'")
        
        return schema


class ToolDiscoveryService:
    """Service for managing tool discovery across multiple tool managers."""
    
    def __init__(self):
        """Initialize tool discovery service."""
        self._managers: Dict[str, MCPToolManager] = {}
    
    def register_manager(self, name: str, manager: MCPToolManager) -> None:
        """Register a tool manager with the service.
        
        Args:
            name: Unique name for the manager
            manager: Tool manager instance
        """
        self._managers[name] = manager
        logger.info(f"Registered tool manager '{name}'")
    
    def unregister_manager(self, name: str) -> None:
        """Unregister a tool manager.
        
        Args:
            name: Name of the manager to unregister
        """
        if name in self._managers:
            del self._managers[name]
            logger.info(f"Unregistered tool manager '{name}'")
    
    async def discover_all_tools(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Discover tools from all registered managers.
        
        Returns:
            Dictionary mapping manager names to their tools
        """
        all_tools = {}
        
        for manager_name, manager in self._managers.items():
            try:
                tools = await manager.discover_tools()
                all_tools[manager_name] = tools
                logger.debug(f"Discovered {len(tools)} tools from manager '{manager_name}'")
            except Exception as e:
                logger.error(f"Failed to discover tools from manager '{manager_name}': {e}")
                all_tools[manager_name] = {}
        
        total_tools = sum(len(tools) for tools in all_tools.values())
        logger.info(f"Discovered {total_tools} total tools from {len(self._managers)} managers")
        
        return all_tools
    
    async def find_tool(self, tool_name: str) -> Optional[MCPToolManager]:
        """Find which manager provides a specific tool.
        
        Args:
            tool_name: Name of the tool to find
            
        Returns:
            Tool manager that provides the tool, or None if not found
        """
        for manager_name, manager in self._managers.items():
            try:
                tools = await manager.discover_tools()
                if tool_name in tools:
                    logger.debug(f"Found tool '{tool_name}' in manager '{manager_name}'")
                    return manager
            except Exception as e:
                logger.error(f"Error checking manager '{manager_name}' for tool '{tool_name}': {e}")
        
        logger.debug(f"Tool '{tool_name}' not found in any registered manager")
        return None
    
    async def execute_tool_anywhere(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool using any available manager.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Normalized tool execution result
            
        Raises:
            ToolExecutionError: If tool not found or execution fails
        """
        manager = await self.find_tool(tool_name)
        if not manager:
            available_managers = list(self._managers.keys())
            raise tool_execution_failed(
                tool_name,
                f"Tool not found in any manager. Available managers: {available_managers}",
                arguments=arguments
            )
        
        return await manager.execute_tool(tool_name, arguments)
    
    def get_manager_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered managers.
        
        Returns:
            Dictionary with manager information
        """
        info = {}
        for manager_name, manager in self._managers.items():
            info[manager_name] = {
                "cache_info": manager.cache_info,
                "available_tools": manager.list_tool_names()
            }
        return info