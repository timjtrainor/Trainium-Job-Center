"""Tests for CrewAI integration with MCP Gateway."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.mcp import (
    MCPGatewayAdapter,
    StreamingTransport,
    AsyncMCPToolWrapper,
    MCPToolWrapper,
    MCPToolFactory,
    MCPError,
    ToolExecutionError
)


class TestAsyncMCPToolWrapper:
    """Test the AsyncMCPToolWrapper class."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock MCP adapter."""
        adapter = Mock(spec=MCPGatewayAdapter)
        adapter.list_tools = AsyncMock()
        adapter.execute_tool = AsyncMock()
        return adapter
    
    @pytest.fixture  
    def sample_tools(self):
        """Sample tools data."""
        return {
            "test_tool": {
                "name": "test_tool",
                "description": "A test tool for testing",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_async_tool_wrapper_initialization(self, mock_adapter, sample_tools):
        """Test async tool wrapper initialization."""
        mock_adapter.list_tools.return_value = sample_tools
        
        wrapper = AsyncMCPToolWrapper(mock_adapter, "test_tool")
        assert wrapper.tool_name == "test_tool"
        assert not wrapper._initialized
        
        await wrapper.initialize()
        
        assert wrapper._initialized
        assert wrapper.tool_info == sample_tools["test_tool"]
        mock_adapter.list_tools.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_async_tool_wrapper_execute(self, mock_adapter, sample_tools):
        """Test async tool execution."""
        mock_adapter.list_tools.return_value = sample_tools
        mock_adapter.execute_tool.return_value = "Test result"
        
        wrapper = AsyncMCPToolWrapper(mock_adapter, "test_tool")
        await wrapper.initialize()
        
        result = await wrapper.execute(query="test query")
        
        assert result == "Test result"
        mock_adapter.execute_tool.assert_called_once_with("test_tool", {"query": "test query"})
    
    @pytest.mark.asyncio
    async def test_async_tool_wrapper_auto_initialize(self, mock_adapter, sample_tools):
        """Test automatic initialization on first execute."""
        mock_adapter.list_tools.return_value = sample_tools
        mock_adapter.execute_tool.return_value = "Auto init result"
        
        wrapper = AsyncMCPToolWrapper(mock_adapter, "test_tool")
        
        # Should auto-initialize on first execute
        result = await wrapper.execute(query="test")
        
        assert result == "Auto init result"
        assert wrapper._initialized
        mock_adapter.list_tools.assert_called_once()
        mock_adapter.execute_tool.assert_called_once_with("test_tool", {"query": "test"})
    
    @pytest.mark.asyncio
    async def test_async_tool_wrapper_tool_not_found(self, mock_adapter):
        """Test error handling when tool is not found."""
        mock_adapter.list_tools.return_value = {}
        
        wrapper = AsyncMCPToolWrapper(mock_adapter, "nonexistent_tool")
        
        with pytest.raises(MCPError, match="Tool 'nonexistent_tool' not found"):
            await wrapper.initialize()
    
    @pytest.mark.asyncio
    async def test_async_tool_wrapper_execution_error(self, mock_adapter, sample_tools):
        """Test error handling during tool execution."""
        mock_adapter.list_tools.return_value = sample_tools
        mock_adapter.execute_tool.side_effect = Exception("Execution failed")
        
        wrapper = AsyncMCPToolWrapper(mock_adapter, "test_tool")
        await wrapper.initialize()
        
        with pytest.raises(ToolExecutionError, match="Tool execution failed"):
            await wrapper.execute(query="test")
    
    def test_get_description_uninitialized(self, mock_adapter):
        """Test get_description before initialization."""
        wrapper = AsyncMCPToolWrapper(mock_adapter, "test_tool")
        description = wrapper.get_description()
        assert "not initialized" in description.lower()
    
    def test_get_description_initialized(self, mock_adapter, sample_tools):
        """Test get_description after initialization."""
        wrapper = AsyncMCPToolWrapper(mock_adapter, "test_tool")
        wrapper.tool_info = sample_tools["test_tool"]
        wrapper._initialized = True
        
        description = wrapper.get_description()
        assert description == "A test tool for testing"
    
    def test_get_schema(self, mock_adapter, sample_tools):
        """Test get_schema method."""
        wrapper = AsyncMCPToolWrapper(mock_adapter, "test_tool")
        wrapper.tool_info = sample_tools["test_tool"]
        wrapper._initialized = True
        
        schema = wrapper.get_schema()
        assert schema == sample_tools["test_tool"]["inputSchema"]


class TestMCPToolWrapper:
    """Test the MCPToolWrapper class for CrewAI compatibility."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock MCP adapter."""
        adapter = Mock(spec=MCPGatewayAdapter)
        adapter.list_tools = AsyncMock()
        adapter.execute_tool = AsyncMock()
        return adapter
    
    @pytest.fixture
    def sample_tools(self):
        """Sample tools data."""
        return {
            "search_tool": {
                "name": "search_tool",
                "description": "Search for information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Result limit"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    def test_crewai_tool_wrapper_creation(self, mock_adapter):
        """Test CrewAI tool wrapper creation."""
        # Mock no running event loop scenario
        with patch('asyncio.get_running_loop', side_effect=RuntimeError()):
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = {"test_tool": {"description": "Test tool"}}
                
                wrapper = MCPToolWrapper(mock_adapter, "test_tool")
                
                assert wrapper.tool_name == "test_tool"
                assert hasattr(wrapper, 'name')
                assert hasattr(wrapper, 'description')
    
    def test_crewai_tool_wrapper_in_event_loop(self, mock_adapter):
        """Test CrewAI tool wrapper creation when event loop is running."""
        # Mock running event loop scenario
        with patch('asyncio.get_running_loop'):
            wrapper = MCPToolWrapper(mock_adapter, "test_tool")
            
            assert wrapper.tool_name == "test_tool"
            assert wrapper.tool_info == {}  # Should be empty when event loop is running
    
    @patch('asyncio.run')
    def test_crewai_tool_wrapper_run(self, mock_run, mock_adapter):
        """Test CrewAI tool _run method."""
        mock_run.return_value = "Tool execution result"
        
        wrapper = MCPToolWrapper(mock_adapter, "test_tool")
        result = wrapper._run(query="test query")
        
        assert result == "Tool execution result"
        # asyncio.run should be called for tool execution
        assert mock_run.called
    
    def test_schema_conversion_basic(self, mock_adapter):
        """Test basic MCP schema to Pydantic conversion."""
        wrapper = MCPToolWrapper(mock_adapter, "test_tool")
        
        mcp_schema = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "count": {
                    "type": "integer", 
                    "description": "Number of results"
                }
            },
            "required": ["query"]
        }
        
        pydantic_model = wrapper._create_schema_from_mcp(mcp_schema)
        
        # Check that model was created
        assert pydantic_model is not None
        assert hasattr(pydantic_model, '__fields__') or hasattr(pydantic_model, 'model_fields')
    
    def test_schema_conversion_empty(self, mock_adapter):
        """Test schema conversion with empty schema."""
        wrapper = MCPToolWrapper(mock_adapter, "test_tool")
        
        pydantic_model = wrapper._create_schema_from_mcp({})
        
        # Should return a basic model
        assert pydantic_model is not None
    
    def test_json_type_conversion(self, mock_adapter):
        """Test JSON type to Python type conversion."""
        wrapper = MCPToolWrapper(mock_adapter, "test_tool")
        
        assert wrapper._json_type_to_python("string") == str
        assert wrapper._json_type_to_python("integer") == int
        assert wrapper._json_type_to_python("number") == float
        assert wrapper._json_type_to_python("boolean") == bool
        assert wrapper._json_type_to_python("unknown") == str  # Default fallback


class TestMCPToolFactory:
    """Test the MCPToolFactory class."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock MCP adapter."""
        adapter = Mock(spec=MCPGatewayAdapter)
        adapter.list_tools = AsyncMock()
        return adapter
    
    @pytest.fixture
    def sample_tools(self):
        """Sample tools data."""
        return {
            "tool1": {"name": "tool1", "description": "First tool"},
            "tool2": {"name": "tool2", "description": "Second tool"},
            "tool3": {"name": "tool3", "description": "Third tool"}
        }
    
    @pytest.mark.asyncio
    async def test_create_async_tools(self, mock_adapter, sample_tools):
        """Test creating async tools via factory."""
        mock_adapter.list_tools.return_value = sample_tools
        
        factory = MCPToolFactory(mock_adapter)
        async_tools = await factory.create_async_tools()
        
        assert len(async_tools) == 3
        assert all(isinstance(tool, AsyncMCPToolWrapper) for tool in async_tools.values())
        assert all(tool._initialized for tool in async_tools.values())
        
        # Check tool names
        assert set(async_tools.keys()) == {"tool1", "tool2", "tool3"}
    
    @pytest.mark.asyncio
    async def test_create_crewai_tools(self, mock_adapter, sample_tools):
        """Test creating CrewAI tools via factory."""
        mock_adapter.list_tools.return_value = sample_tools
        
        factory = MCPToolFactory(mock_adapter)
        crewai_tools = await factory.create_crewai_tools()
        
        assert len(crewai_tools) == 3
        assert all(isinstance(tool, MCPToolWrapper) for tool in crewai_tools.values())
        
        # Check tool names
        assert set(crewai_tools.keys()) == {"tool1", "tool2", "tool3"}
    
    @pytest.mark.asyncio
    async def test_create_single_async_tool(self, mock_adapter, sample_tools):
        """Test creating a single async tool."""
        mock_adapter.list_tools.return_value = sample_tools
        
        factory = MCPToolFactory(mock_adapter)
        tool = await factory.create_single_async_tool("tool1")
        
        assert isinstance(tool, AsyncMCPToolWrapper)
        assert tool.tool_name == "tool1"
        assert tool._initialized
    
    def test_create_single_crewai_tool(self, mock_adapter):
        """Test creating a single CrewAI tool."""
        factory = MCPToolFactory(mock_adapter)
        tool = factory.create_single_crewai_tool("test_tool")
        
        assert isinstance(tool, MCPToolWrapper)
        assert tool.tool_name == "test_tool"
    
    @pytest.mark.asyncio
    async def test_factory_error_handling(self, mock_adapter):
        """Test factory error handling."""
        mock_adapter.list_tools.side_effect = Exception("Connection failed")
        
        factory = MCPToolFactory(mock_adapter)
        
        with pytest.raises(MCPError, match="Async tool creation failed"):
            await factory.create_async_tools()
        
        with pytest.raises(MCPError, match="CrewAI tool creation failed"):
            await factory.create_crewai_tools()


class TestIntegrationScenarios:
    """Test integration scenarios and real-world usage patterns."""
    
    @pytest.fixture
    def mock_transport(self):
        """Create a mock transport."""
        transport = Mock(spec=StreamingTransport)
        return transport
    
    @pytest.fixture
    def mock_adapter_with_tools(self):
        """Create a mock adapter with realistic tool data."""
        adapter = Mock(spec=MCPGatewayAdapter)
        
        sample_tools = {
            "web_search": {
                "name": "web_search",
                "description": "Search the web for information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Result limit"}
                    },
                    "required": ["query"]
                }
            },
            "calculator": {
                "name": "calculator", 
                "description": "Perform mathematical calculations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "Math expression"}
                    },
                    "required": ["expression"]
                }
            }
        }
        
        adapter.list_tools = AsyncMock(return_value=sample_tools)
        adapter.execute_tool = AsyncMock()
        adapter.is_connected = Mock(return_value=True)
        
        return adapter
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, mock_adapter_with_tools):
        """Test end-to-end workflow from adapter to tool execution."""
        # Create factory
        factory = MCPToolFactory(mock_adapter_with_tools)
        
        # Create tools
        async_tools = await factory.create_async_tools()
        crewai_tools = await factory.create_crewai_tools()
        
        # Verify both types created
        assert len(async_tools) == 2
        assert len(crewai_tools) == 2
        
        # Test async tool execution
        web_search_async = async_tools["web_search"]
        mock_adapter_with_tools.execute_tool.return_value = "Search results..."
        
        result = await web_search_async.execute(query="test search")
        assert result == "Search results..."
        
        # Test CrewAI tool execution
        web_search_crewai = crewai_tools["web_search"]
        
        with patch('asyncio.run', return_value="CrewAI search results"):
            result = web_search_crewai._run(query="test search")
            assert result == "CrewAI search results"
    
    @pytest.mark.asyncio
    async def test_error_propagation(self, mock_adapter_with_tools):
        """Test that errors are properly propagated through the tool chain."""
        factory = MCPToolFactory(mock_adapter_with_tools)
        
        # Test async tool error propagation
        async_tools = await factory.create_async_tools()
        web_search = async_tools["web_search"]
        
        mock_adapter_with_tools.execute_tool.side_effect = Exception("Network error")
        
        with pytest.raises(ToolExecutionError, match="Tool execution failed"):
            await web_search.execute(query="test")
        
        # Test CrewAI tool error propagation
        crewai_tools = await factory.create_crewai_tools()
        crewai_search = crewai_tools["web_search"]
        
        with patch('asyncio.run', side_effect=Exception("Network error")):
            with pytest.raises(ToolExecutionError, match="Tool execution failed"):
                crewai_search._run(query="test")
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_usage(self, mock_adapter_with_tools):
        """Test concurrent usage of multiple tools."""
        factory = MCPToolFactory(mock_adapter_with_tools)
        async_tools = await factory.create_async_tools()
        
        # Mock different return values for different tools
        def mock_execute_tool(tool_name, args):
            return f"Result from {tool_name}: {args}"
        
        mock_adapter_with_tools.execute_tool.side_effect = mock_execute_tool
        
        # Execute tools concurrently
        tasks = [
            async_tools["web_search"].execute(query="search1"),
            async_tools["calculator"].execute(expression="2+2"),
            async_tools["web_search"].execute(query="search2")
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert "web_search" in results[0]
        assert "calculator" in results[1] 
        assert "web_search" in results[2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])