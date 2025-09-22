"""Tests for MCP Tool Manager and Result Normalizer.

Test suite for tool discovery, execution, argument validation,
result normalization, and error handling.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Import MCP modules
from app.services.mcp.mcp_tools import MCPToolManager, ToolDiscoveryService
from app.services.mcp.mcp_results import ResultNormalizer
from app.services.mcp.mcp_protocol import MCPProtocol
from app.services.mcp.mcp_transport import MCPTransport
from app.services.mcp.mcp_models import (
    ToolInfo, ToolListResponse, ToolCallRequest, ToolCallResponse
)
from app.services.mcp.mcp_exceptions import (
    ToolExecutionError, ProtocolError, TimeoutError
)


class MockTransport(MCPTransport):
    """Mock transport for testing tool operations."""
    
    def __init__(self):
        super().__init__()
        self.sent_messages = []
        self.response_queue = []
        self.should_fail = False
        self.should_timeout = False
        self._next_response_id = 1
        
    async def connect(self):
        if self.should_fail:
            raise Exception("Mock connection failure")
        self._connected = True
        
    async def disconnect(self):
        self._connected = False
        
    async def send_message(self, message: Dict[str, Any]):
        if self.should_timeout:
            await asyncio.sleep(100)
        self.sent_messages.append(message)
        
    async def receive_message(self) -> Dict[str, Any]:
        if self.should_timeout:
            await asyncio.sleep(100)
        if not self.response_queue:
            raise Exception("No responses queued")
        response = self.response_queue.pop(0)
        
        # Auto-fix response ID to match the expected request ID
        if "id" in response:
            # Find the corresponding sent message to get the correct ID
            if self.sent_messages:
                last_request = self.sent_messages[-1]
                if "id" in last_request:
                    response["id"] = last_request["id"]
        
        return response
        
    def queue_response(self, response_template: Dict[str, Any]):
        """Queue a response template for the next receive_message call."""
        self.response_queue.append(response_template.copy())


@pytest.fixture
def mock_transport():
    """Create mock transport for testing."""
    return MockTransport()


@pytest.fixture
def protocol(mock_transport):
    """Create MCP protocol instance with mock transport."""
    return MCPProtocol(mock_transport, timeout=1)


@pytest.fixture
def tool_manager(protocol):
    """Create tool manager instance."""
    return MCPToolManager(protocol, cache_ttl=10)


@pytest.fixture
def sample_tools():
    """Sample tools for testing."""
    return {
        "duckduckgo_search": {
            "name": "duckduckgo_search",
            "description": "Search the web using DuckDuckGo",
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
        },
        "calculator": {
            "name": "calculator",
            "description": "Perform mathematical calculations",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression"
                    }
                },
                "required": ["expression"]
            }
        }
    }


class TestMCPToolManager:
    """Test cases for MCP tool manager."""
    
    @pytest.mark.asyncio
    async def test_tool_discovery(self, tool_manager, mock_transport, sample_tools):
        """Test tool discovery and caching."""
        # Queue tools/list response
        tools_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    sample_tools["duckduckgo_search"],
                    sample_tools["calculator"]
                ]
            }
        }
        mock_transport.queue_response(tools_response)
        
        # Test discovery
        tools = await tool_manager.discover_tools()
        
        # Verify results
        assert len(tools) == 2
        assert "duckduckgo_search" in tools
        assert "calculator" in tools
        assert tools["duckduckgo_search"]["description"] == "Search the web using DuckDuckGo"
        
        # Verify request was sent
        assert len(mock_transport.sent_messages) == 1
        sent_msg = mock_transport.sent_messages[0]
        assert sent_msg["method"] == "tools/list"
        
        # Test cache hit (no new request)
        tools_cached = await tool_manager.discover_tools()
        assert tools_cached == tools
        assert len(mock_transport.sent_messages) == 1  # No additional request
        
    @pytest.mark.asyncio
    async def test_tool_discovery_empty_list(self, tool_manager, mock_transport):
        """Test discovery with empty tool list."""
        # Queue empty tools response
        empty_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": []
            }
        }
        mock_transport.queue_response(empty_response)
        
        # Test discovery
        tools = await tool_manager.discover_tools()
        
        # Verify empty result
        assert tools == {}
        assert tool_manager.list_tool_names() == []
        
    @pytest.mark.asyncio
    async def test_get_tool_info(self, tool_manager, mock_transport, sample_tools):
        """Test getting specific tool information."""
        # Setup discovery
        tools_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [sample_tools["duckduckgo_search"]]
            }
        }
        mock_transport.queue_response(tools_response)
        
        # Test get tool info
        tool_info = await tool_manager.get_tool_info("duckduckgo_search")
        
        assert tool_info["name"] == "duckduckgo_search"
        assert tool_info["description"] == "Search the web using DuckDuckGo"
        assert "inputSchema" in tool_info
        
    @pytest.mark.asyncio
    async def test_get_tool_info_not_found(self, tool_manager, mock_transport):
        """Test getting info for non-existent tool."""
        # Setup empty discovery
        empty_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"tools": []}
        }
        mock_transport.queue_response(empty_response)
        
        # Test should raise ToolExecutionError
        with pytest.raises(ToolExecutionError) as excinfo:
            await tool_manager.get_tool_info("nonexistent_tool")
            
        assert "Tool not found" in str(excinfo.value)
        assert excinfo.value.tool_name == "nonexistent_tool"
        
    @pytest.mark.asyncio
    async def test_tool_execution_success(self, tool_manager, mock_transport, sample_tools):
        """Test successful tool execution."""
        # Setup discovery
        tools_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [sample_tools["duckduckgo_search"]]
            }
        }
        mock_transport.queue_response(tools_response)
        
        # Setup tool execution response
        execution_response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Search results for 'python programming':\n1. Python.org - Official Python website\n2. Python Tutorial - Learn Python"
                    }
                ],
                "isError": False
            }
        }
        mock_transport.queue_response(execution_response)
        
        # Execute tool
        result = await tool_manager.execute_tool("duckduckgo_search", {"query": "python programming"})
        
        # Verify result
        assert result["success"] is True
        assert "Search results" in result["content"]
        assert result["error"] is None
        assert result["metadata"]["tool_name"] == "duckduckgo_search"
        assert "execution_time" in result["metadata"]
        
        # Verify tool call request
        assert len(mock_transport.sent_messages) == 2
        call_request = mock_transport.sent_messages[1]
        assert call_request["method"] == "tools/call"
        assert call_request["params"]["name"] == "duckduckgo_search"
        assert call_request["params"]["arguments"]["query"] == "python programming"
        
    @pytest.mark.asyncio
    async def test_tool_execution_error(self, tool_manager, mock_transport, sample_tools):
        """Test tool execution error handling."""
        # Setup discovery
        tools_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [sample_tools["calculator"]]
            }
        }
        mock_transport.queue_response(tools_response)
        
        # Setup error response
        error_response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Invalid mathematical expression: 'not a math expression'"
                    }
                ],
                "isError": True
            }
        }
        mock_transport.queue_response(error_response)
        
        # Execute tool should raise ToolExecutionError
        with pytest.raises(ToolExecutionError) as excinfo:
            await tool_manager.execute_tool("calculator", {"expression": "not a math expression"})
            
        assert "Invalid mathematical expression" in str(excinfo.value)
        assert excinfo.value.tool_name == "calculator"
        
    @pytest.mark.asyncio
    async def test_argument_validation_success(self, tool_manager, mock_transport, sample_tools):
        """Test successful argument validation."""
        # Setup discovery
        tools_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [sample_tools["duckduckgo_search"]]
            }
        }
        mock_transport.queue_response(tools_response)
        
        # Test validation without execution
        is_valid = await tool_manager.validate_tool_arguments("duckduckgo_search", {"query": "test"})
        assert is_valid is True
        
    @pytest.mark.asyncio
    async def test_argument_validation_failure(self, tool_manager, mock_transport, sample_tools):
        """Test argument validation failure."""
        # Setup discovery
        tools_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [sample_tools["duckduckgo_search"]]
            }
        }
        mock_transport.queue_response(tools_response)
        
        # Test validation with missing required argument
        with pytest.raises(ToolExecutionError) as excinfo:
            await tool_manager.validate_tool_arguments("duckduckgo_search", {})
            
        assert "Invalid arguments" in str(excinfo.value)
        assert "'query' is a required property" in str(excinfo.value)
        
    @pytest.mark.asyncio
    async def test_cache_expiration(self, tool_manager, mock_transport, sample_tools):
        """Test cache TTL and expiration."""
        # Create tool manager with very short TTL
        short_ttl_manager = MCPToolManager(tool_manager.protocol, cache_ttl=0.1)
        
        # Setup discovery
        tools_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [sample_tools["duckduckgo_search"]]
            }
        }
        mock_transport.queue_response(tools_response)
        
        # Initial discovery
        tools1 = await short_ttl_manager.discover_tools()
        assert len(tools1) == 1
        
        # Wait for cache to expire
        await asyncio.sleep(0.2)
        
        # Setup second response
        mock_transport.queue_response(tools_response)
        
        # Should trigger new discovery
        tools2 = await short_ttl_manager.discover_tools()
        assert len(tools2) == 1
        
        # Should have sent two requests (cache expired)
        assert len(mock_transport.sent_messages) == 2
        
    @pytest.mark.asyncio
    async def test_list_tool_names(self, tool_manager, mock_transport, sample_tools):
        """Test listing available tool names."""
        # Test before discovery
        assert tool_manager.list_tool_names() == []
        
        # Setup discovery
        tools_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    sample_tools["duckduckgo_search"],
                    sample_tools["calculator"]
                ]
            }
        }
        mock_transport.queue_response(tools_response)
        
        # Discover tools
        await tool_manager.discover_tools()
        
        # Test after discovery
        tool_names = tool_manager.list_tool_names()
        assert set(tool_names) == {"duckduckgo_search", "calculator"}
        
    @pytest.mark.asyncio
    async def test_clear_cache(self, tool_manager, mock_transport, sample_tools):
        """Test cache clearing."""
        # Setup discovery
        tools_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [sample_tools["duckduckgo_search"]]
            }
        }
        mock_transport.queue_response(tools_response)
        
        # Discover tools
        await tool_manager.discover_tools()
        assert len(tool_manager.list_tool_names()) == 1
        
        # Clear cache
        tool_manager.clear_cache()
        assert tool_manager.list_tool_names() == []
        
        # Should need to discover again
        mock_transport.queue_response(tools_response)
        await tool_manager.discover_tools()
        assert len(mock_transport.sent_messages) == 2  # Two discovery requests
        
    @pytest.mark.asyncio
    async def test_get_tool_schema(self, tool_manager, mock_transport, sample_tools):
        """Test getting tool input schema."""
        # Setup discovery
        tools_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [sample_tools["duckduckgo_search"]]
            }
        }
        mock_transport.queue_response(tools_response)
        
        # Get schema
        schema = await tool_manager.get_tool_schema("duckduckgo_search")
        
        assert schema is not None
        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert schema["required"] == ["query"]
        
    def test_cache_info(self, tool_manager):
        """Test cache information reporting."""
        # Before discovery
        info = tool_manager.cache_info
        assert info["cached"] is False
        assert info["tool_count"] == 0
        assert info["valid"] is False
        
        # After manual cache setup
        tool_manager.tools_cache = {"test": {}}
        tool_manager.cache_timestamp = time.time()
        
        info = tool_manager.cache_info
        assert info["cached"] is True
        assert info["tool_count"] == 1
        assert info["valid"] is True


class TestResultNormalizer:
    """Test cases for result normalization."""
    
    def test_normalize_success_result(self):
        """Test normalizing successful tool result."""
        raw_result = {
            "content": [
                {
                    "type": "text",
                    "text": "This is a successful result"
                }
            ],
            "isError": False
        }
        
        normalized = ResultNormalizer.normalize_result(raw_result)
        
        assert normalized["success"] is True
        assert normalized["content"] == "This is a successful result"
        assert normalized["error"] is None
        assert len(normalized["raw_content"]) == 1
        assert normalized["metadata"]["content_count"] == 1
        
    def test_normalize_error_result(self):
        """Test normalizing error tool result."""
        raw_result = {
            "content": [
                {
                    "type": "text",
                    "text": "Tool execution failed: invalid input"
                }
            ],
            "isError": True
        }
        
        normalized = ResultNormalizer.normalize_result(raw_result)
        
        assert normalized["success"] is False
        assert normalized["content"] == "Tool execution failed: invalid input"
        assert normalized["error"] == "Tool execution failed: invalid input"
        
    def test_extract_text_content_multiple_items(self):
        """Test extracting text from multiple content items."""
        result = {
            "content": [
                {"type": "text", "text": "First part"},
                {"type": "text", "text": "Second part"},
                {"type": "unknown", "text": "Unknown type"}
            ]
        }
        
        text = ResultNormalizer.extract_text_content(result)
        assert text == "First part\nSecond part\nUnknown type"
        
    def test_extract_text_content_resource_type(self):
        """Test extracting text from resource content."""
        result = {
            "content": [
                {
                    "type": "resource",
                    "resource": {
                        "text": "Resource content"
                    }
                }
            ]
        }
        
        text = ResultNormalizer.extract_text_content(result)
        assert text == "Resource content"
        
    def test_extract_error_details_explicit_error(self):
        """Test extracting error details from explicit error content."""
        result = {
            "content": [
                {
                    "type": "error",
                    "message": "Specific error message"
                }
            ],
            "isError": True
        }
        
        error_msg = ResultNormalizer.extract_error_details(result)
        assert error_msg == "Specific error message"
        
    def test_extract_error_details_no_error(self):
        """Test extracting error details when no error present."""
        result = {
            "content": [
                {"type": "text", "text": "Success message"}
            ],
            "isError": False
        }
        
        error_msg = ResultNormalizer.extract_error_details(result)
        assert error_msg is None
        
    def test_validate_tool_response_valid(self):
        """Test validating valid tool response."""
        response = {
            "content": [
                {"type": "text", "text": "Valid response"}
            ],
            "isError": False
        }
        
        is_valid = ResultNormalizer.validate_tool_response(response)
        assert is_valid is True
        
    def test_validate_tool_response_invalid(self):
        """Test validating invalid tool response."""
        # Missing content field
        response = {
            "isError": False
        }
        
        is_valid = ResultNormalizer.validate_tool_response(response)
        assert is_valid is False
        
        # Content not a list
        response = {
            "content": "not a list"
        }
        
        is_valid = ResultNormalizer.validate_tool_response(response)
        assert is_valid is False
        
    def test_create_error_result(self):
        """Test creating error result."""
        error_result = ResultNormalizer.create_error_result("Test error", "test_tool")
        
        assert error_result["success"] is False
        assert error_result["content"] == "Test error"
        assert error_result["error"] == "Test error"
        assert error_result["metadata"]["tool_name"] == "test_tool"
        assert error_result["metadata"]["error_created"] is True
        
    def test_create_success_result(self):
        """Test creating success result."""
        success_result = ResultNormalizer.create_success_result("Success message")
        
        assert success_result["success"] is True
        assert success_result["content"] == "Success message"
        assert success_result["error"] is None
        assert success_result["metadata"]["success_created"] is True


class TestToolDiscoveryService:
    """Test cases for tool discovery service."""
    
    @pytest.fixture
    def discovery_service(self):
        """Create tool discovery service."""
        return ToolDiscoveryService()
        
    @pytest.fixture
    def mock_manager1(self):
        """Create first mock tool manager."""
        manager = AsyncMock(spec=MCPToolManager)
        manager.discover_tools.return_value = {
            "tool1": {"name": "tool1", "description": "Tool 1"}
        }
        manager.list_tool_names.return_value = ["tool1"]
        manager.cache_info = {"cached": True, "tool_count": 1}
        return manager
        
    @pytest.fixture
    def mock_manager2(self):
        """Create second mock tool manager."""
        manager = AsyncMock(spec=MCPToolManager)
        manager.discover_tools.return_value = {
            "tool2": {"name": "tool2", "description": "Tool 2"}
        }
        manager.list_tool_names.return_value = ["tool2"]
        manager.cache_info = {"cached": True, "tool_count": 1}
        return manager
        
    def test_register_unregister_manager(self, discovery_service, mock_manager1):
        """Test registering and unregistering managers."""
        # Register manager
        discovery_service.register_manager("manager1", mock_manager1)
        assert "manager1" in discovery_service._managers
        
        # Unregister manager
        discovery_service.unregister_manager("manager1")
        assert "manager1" not in discovery_service._managers
        
    @pytest.mark.asyncio
    async def test_discover_all_tools(self, discovery_service, mock_manager1, mock_manager2):
        """Test discovering tools from all managers."""
        # Register managers
        discovery_service.register_manager("manager1", mock_manager1)
        discovery_service.register_manager("manager2", mock_manager2)
        
        # Discover all tools
        all_tools = await discovery_service.discover_all_tools()
        
        assert len(all_tools) == 2
        assert "manager1" in all_tools
        assert "manager2" in all_tools
        assert "tool1" in all_tools["manager1"]
        assert "tool2" in all_tools["manager2"]
        
    @pytest.mark.asyncio
    async def test_find_tool(self, discovery_service, mock_manager1, mock_manager2):
        """Test finding which manager provides a tool."""
        # Register managers
        discovery_service.register_manager("manager1", mock_manager1)
        discovery_service.register_manager("manager2", mock_manager2)
        
        # Find existing tool
        manager = await discovery_service.find_tool("tool1")
        assert manager == mock_manager1
        
        # Find non-existing tool
        manager = await discovery_service.find_tool("nonexistent")
        assert manager is None
        
    @pytest.mark.asyncio
    async def test_execute_tool_anywhere(self, discovery_service, mock_manager1):
        """Test executing tool using any available manager."""
        # Setup mock manager
        mock_manager1.execute_tool.return_value = {
            "success": True,
            "content": "Tool executed successfully"
        }
        
        # Register manager
        discovery_service.register_manager("manager1", mock_manager1)
        
        # Execute tool
        result = await discovery_service.execute_tool_anywhere("tool1", {"arg": "value"})
        
        assert result["success"] is True
        mock_manager1.execute_tool.assert_called_once_with("tool1", {"arg": "value"})
        
    @pytest.mark.asyncio
    async def test_execute_tool_anywhere_not_found(self, discovery_service, mock_manager1):
        """Test executing non-existent tool."""
        # Register manager
        discovery_service.register_manager("manager1", mock_manager1)
        
        # Try to execute non-existent tool
        with pytest.raises(ToolExecutionError) as excinfo:
            await discovery_service.execute_tool_anywhere("nonexistent", {})
            
        assert "Tool not found in any manager" in str(excinfo.value)
        
    def test_get_manager_info(self, discovery_service, mock_manager1):
        """Test getting manager information."""
        # Register manager
        discovery_service.register_manager("manager1", mock_manager1)
        
        # Get info
        info = discovery_service.get_manager_info()
        
        assert "manager1" in info
        assert "cache_info" in info["manager1"]
        assert "available_tools" in info["manager1"]


class TestUnknownToolHandling:
    """Test cases for unknown tool handling."""
    
    @pytest.mark.asyncio
    async def test_unknown_tool_execution(self, tool_manager, mock_transport):
        """Test handling of unknown tool execution."""
        # Setup empty discovery
        empty_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"tools": []}
        }
        mock_transport.queue_response(empty_response)
        
        # Try to execute unknown tool
        with pytest.raises(ToolExecutionError) as excinfo:
            await tool_manager.execute_tool("unknown_tool", {"arg": "value"})
            
        assert "Tool not found" in str(excinfo.value)
        assert excinfo.value.tool_name == "unknown_tool"
        
    @pytest.mark.asyncio
    async def test_unknown_tool_info(self, tool_manager, mock_transport):
        """Test getting info for unknown tool."""
        # Setup empty discovery
        empty_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"tools": []}
        }
        mock_transport.queue_response(empty_response)
        
        # Try to get info for unknown tool
        with pytest.raises(ToolExecutionError) as excinfo:
            await tool_manager.get_tool_info("unknown_tool")
            
        assert "Tool not found" in str(excinfo.value)
        assert "Available tools: []" in str(excinfo.value)