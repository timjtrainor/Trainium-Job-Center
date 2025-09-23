"""CrewAI Integration for MCP Gateway Adapter.

This module provides CrewAI-compatible wrappers for MCP tools, enabling
seamless integration between CrewAI agents and MCP gateway functionality.

Key Components:
- AsyncMCPToolWrapper: Async-native wrapper (PREFERRED)
- MCPToolWrapper: Sync wrapper for CrewAI compatibility
- MCPToolFactory: Factory for creating tool wrappers
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Type, Optional, List
import asyncio
import logging

# Optional CrewAI imports - graceful fallback if not available
try:
    from crewai_tools import BaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Create a basic BaseTool class for compatibility
    class BaseTool:
        def __init__(self, name: str, description: str, args_schema: Type = None):
            self.name = name
            self.description = description
            self.args_schema = args_schema
        
        def _run(self, **kwargs) -> str:
            raise NotImplementedError("Subclasses must implement _run method")

# Optional Pydantic imports
try:
    from pydantic import BaseModel, Field, create_model
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Basic compatibility classes
    class BaseModel:
        pass
    
    def Field(**kwargs):
        return None
    
    def create_model(name: str, **fields):
        return type(name, (BaseModel,), {})

from .mcp_adapter import MCPGatewayAdapter
from .mcp_exceptions import MCPError, ToolExecutionError

# Set up logging
logger = logging.getLogger(__name__)


class AsyncMCPToolWrapper:
    """Async-native wrapper for frameworks that support async tools (PREFERRED).
    
    This wrapper provides direct async access to MCP tools without the overhead
    of thread pool execution, making it ideal for async-native frameworks.
    """
    
    def __init__(self, mcp_adapter: MCPGatewayAdapter, tool_name: str):
        """Initialize the async tool wrapper.
        
        Args:
            mcp_adapter: Connected MCP gateway adapter
            tool_name: Name of the MCP tool to wrap
        """
        self.mcp_adapter = mcp_adapter
        self.tool_name = tool_name
        self.tool_info: Dict[str, Any] = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize tool metadata (call after adapter connection).
        
        Raises:
            MCPError: If tool initialization fails
        """
        if self._initialized:
            return
            
        try:
            # Get tool information from the adapter
            tools = await self.mcp_adapter.list_tools()
            if self.tool_name not in tools:
                raise MCPError(f"Tool '{self.tool_name}' not found in available tools")
            
            self.tool_info = tools[self.tool_name]
            self._initialized = True
            
            logger.debug(f"Initialized async wrapper for tool: {self.tool_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize async tool wrapper for {self.tool_name}: {e}")
            raise MCPError(f"Tool initialization failed: {e}")
        
    async def execute(self, **kwargs) -> str:
        """Execute the MCP tool asynchronously.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result as string
            
        Raises:
            MCPError: If tool execution fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            result = await self.mcp_adapter.execute_tool(self.tool_name, kwargs)
            logger.debug(f"Async tool {self.tool_name} executed successfully")
            return str(result)
            
        except Exception as e:
            logger.error(f"Async tool {self.tool_name} execution failed: {e}")
            raise ToolExecutionError(f"Tool execution failed: {e}")
        
    def get_description(self) -> str:
        """Get tool description for AI frameworks.
        
        Returns:
            Tool description string
        """
        if not self._initialized:
            return f"MCP tool: {self.tool_name} (not initialized)"
        
        return self.tool_info.get("description", f"MCP tool: {self.tool_name}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool input schema.
        
        Returns:
            Tool input schema dictionary
        """
        if not self._initialized:
            return {}
        
        return self.tool_info.get("inputSchema", {})


class MCPToolWrapper(BaseTool):
    """Sync wrapper for CrewAI compatibility (use only if async not supported).
    
    This wrapper converts async MCP tool calls to synchronous ones using
    a thread pool executor for compatibility with CrewAI's sync tool interface.
    
    Note: Requires crewai_tools to be installed for full functionality.
    """
    
    def __init__(self, mcp_adapter: MCPGatewayAdapter, tool_name: str):
        """Initialize the CrewAI-compatible tool wrapper.
        
        Args:
            mcp_adapter: Connected MCP gateway adapter  
            tool_name: Name of the MCP tool to wrap
        """
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not available - MCPToolWrapper will have limited functionality")
        
        self.mcp_adapter = mcp_adapter
        self.tool_name = tool_name
        self._executor = ThreadPoolExecutor(max_workers=1)
        self.tool_info: Dict[str, Any] = {}
        
        # Try to get tool metadata - handle event loop scenarios
        try:
            loop = asyncio.get_running_loop()
            # We're in an event loop, will populate during first use
            self.tool_info = {}
            logger.debug(f"CrewAI wrapper for {tool_name} created (will initialize on first use)")
        except RuntimeError:
            # No event loop, safe to initialize synchronously
            try:
                self.tool_info = asyncio.run(self._get_tool_info())
                logger.debug(f"CrewAI wrapper for {tool_name} initialized synchronously")
            except Exception as e:
                logger.warning(f"Failed to initialize tool info for {tool_name}: {e}")
                self.tool_info = {}
        
        # Initialize parent class if CrewAI is available
        if CREWAI_AVAILABLE:
            super().__init__(
                name=self.tool_info.get("name", tool_name),
                description=self.tool_info.get("description", f"MCP tool: {tool_name}"),
                args_schema=self._create_schema_from_mcp(
                    self.tool_info.get("inputSchema", {})
                )
            )
        else:
            # Basic initialization for compatibility
            self.name = self.tool_info.get("name", tool_name)
            self.description = self.tool_info.get("description", f"MCP tool: {tool_name}")
            self.args_schema = None
        
    async def _get_tool_info(self) -> Dict[str, Any]:
        """Get tool information from MCP adapter."""
        tools = await self.mcp_adapter.list_tools()
        if self.tool_name not in tools:
            raise MCPError(f"Tool '{self.tool_name}' not found")
        return tools[self.tool_name]
        
    def _run(self, **kwargs) -> str:
        """Execute the MCP tool synchronously for CrewAI.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result as string
        """
        try:
            # If tool info is empty, try to get it now
            if not self.tool_info:
                try:
                    self.tool_info = asyncio.run(self._get_tool_info())
                except Exception as e:
                    logger.warning(f"Could not get tool info during execution: {e}")
            
            # Execute the tool asynchronously in a new event loop
            result = asyncio.run(self.mcp_adapter.execute_tool(self.tool_name, kwargs))
            logger.debug(f"CrewAI tool {self.tool_name} executed successfully")
            return str(result)
            
        except Exception as e:
            logger.error(f"CrewAI tool {self.tool_name} execution failed: {e}")
            raise ToolExecutionError(f"Tool execution failed: {e}")
        
    def _create_schema_from_mcp(self, mcp_schema: Dict[str, Any]) -> Type[BaseModel]:
        """Convert MCP input schema to Pydantic model.
        
        Args:
            mcp_schema: MCP JSON schema for tool inputs
            
        Returns:
            Pydantic model class for tool arguments
        """
        if not PYDANTIC_AVAILABLE:
            logger.warning("Pydantic not available - schema conversion limited")
            return create_model(f"{self.tool_name}Args")
        
        if not mcp_schema or not isinstance(mcp_schema, dict):
            # Return a basic schema if none provided
            return create_model(f"{self.tool_name}Args")
        
        properties = mcp_schema.get("properties", {})
        required = mcp_schema.get("required", [])
        
        # Convert JSON schema properties to Pydantic fields
        fields = {}
        for prop_name, prop_schema in properties.items():
            field_type = self._json_type_to_python(prop_schema.get("type", "string"))
            field_description = prop_schema.get("description", "")
            
            if prop_name in required:
                fields[prop_name] = (field_type, Field(description=field_description))
            else:
                fields[prop_name] = (Optional[field_type], Field(default=None, description=field_description))
        
        # Create dynamic Pydantic model
        model_name = f"{self.tool_name.title().replace('_', '')}Args"
        return create_model(model_name, **fields)
    
    def _json_type_to_python(self, json_type: str) -> Type:
        """Convert JSON schema type to Python type.
        
        Args:
            json_type: JSON schema type string
            
        Returns:
            Corresponding Python type
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": List[str],  # Simplified - assume string arrays
            "object": Dict[str, Any]
        }
        
        return type_mapping.get(json_type, str)


class MCPToolFactory:
    """Factory for creating MCP tool wrappers.
    
    This factory simplifies the creation of tool wrappers and provides
    batch operations for working with multiple tools.
    """
    
    def __init__(self, mcp_adapter: MCPGatewayAdapter):
        """Initialize the tool factory.
        
        Args:
            mcp_adapter: Connected MCP gateway adapter
        """
        self.adapter = mcp_adapter
        
    async def create_async_tools(self) -> Dict[str, AsyncMCPToolWrapper]:
        """Create async wrappers for all available tools.
        
        Returns:
            Dictionary mapping tool names to async wrappers
            
        Raises:
            MCPError: If tool discovery fails
        """
        try:
            tools = await self.adapter.list_tools()
            async_tools = {}
            
            for tool_name in tools.keys():
                wrapper = AsyncMCPToolWrapper(self.adapter, tool_name)
                await wrapper.initialize()
                async_tools[tool_name] = wrapper
                
            logger.info(f"Created {len(async_tools)} async tool wrappers")
            return async_tools
            
        except Exception as e:
            logger.error(f"Failed to create async tools: {e}")
            raise MCPError(f"Async tool creation failed: {e}")
        
    async def create_crewai_tools(self) -> Dict[str, MCPToolWrapper]:
        """Create CrewAI-compatible tools for all available tools.
        
        Returns:
            Dictionary mapping tool names to CrewAI wrappers
            
        Raises:
            MCPError: If tool discovery fails
        """
        try:
            tools = await self.adapter.list_tools()
            crewai_tools = {}
            
            for tool_name in tools.keys():
                wrapper = MCPToolWrapper(self.adapter, tool_name)
                crewai_tools[tool_name] = wrapper
                
            logger.info(f"Created {len(crewai_tools)} CrewAI tool wrappers")
            return crewai_tools
            
        except Exception as e:
            logger.error(f"Failed to create CrewAI tools: {e}")
            raise MCPError(f"CrewAI tool creation failed: {e}")
    
    async def create_single_async_tool(self, tool_name: str) -> AsyncMCPToolWrapper:
        """Create a single async tool wrapper.
        
        Args:
            tool_name: Name of the tool to wrap
            
        Returns:
            Initialized async tool wrapper
            
        Raises:
            MCPError: If tool creation fails
        """
        wrapper = AsyncMCPToolWrapper(self.adapter, tool_name)
        await wrapper.initialize()
        return wrapper
    
    def create_single_crewai_tool(self, tool_name: str) -> MCPToolWrapper:
        """Create a single CrewAI-compatible tool wrapper.
        
        Args:
            tool_name: Name of the tool to wrap
            
        Returns:
            CrewAI tool wrapper
        """
        return MCPToolWrapper(self.adapter, tool_name)


# Utility functions for checking availability
def is_crewai_available() -> bool:
    """Check if CrewAI is available for use.
    
    Returns:
        True if CrewAI dependencies are available, False otherwise
    """
    return CREWAI_AVAILABLE


def is_pydantic_available() -> bool:
    """Check if Pydantic is available for schema conversion.
    
    Returns:
        True if Pydantic is available, False otherwise
    """
    return PYDANTIC_AVAILABLE


def get_integration_status() -> Dict[str, Any]:
    """Get the status of all integration dependencies.
    
    Returns:
        Dictionary with dependency availability status
    """
    return {
        "crewai_available": CREWAI_AVAILABLE,
        "pydantic_available": PYDANTIC_AVAILABLE,
        "full_functionality": CREWAI_AVAILABLE and PYDANTIC_AVAILABLE,
        "async_tools_available": True,  # Always available
        "sync_tools_available": CREWAI_AVAILABLE
    }