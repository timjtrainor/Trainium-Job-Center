#!/usr/bin/env python3
"""
Phase 3 Integration Test - Tool Discovery and Execution

This script tests the new Phase 3 functionality against the actual MCP gateway
to ensure the tool discovery and execution features work correctly.
"""

import asyncio
import json
import logging
import httpx
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our MCP modules
from app.services.mcp import (
    MCPProtocol, StreamingTransport, MCPToolManager, 
    create_mcp_session, ToolDiscoveryService, ResultNormalizer
)


async def test_gateway_health():
    """Test that MCP gateway is running and healthy."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8811/health", timeout=5.0)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"Gateway health check passed: {health_data}")
                return True
            else:
                logger.error(f"Gateway health check failed: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Could not reach gateway: {e}")
        return False


async def test_tool_discovery():
    """Test tool discovery functionality."""
    logger.info("Testing tool discovery...")
    
    try:
        # Create transport and protocol
        transport = StreamingTransport("http://localhost:8811")
        protocol = MCPProtocol(transport, timeout=10)
        
        # Create tool manager
        tool_manager = MCPToolManager(protocol, cache_ttl=60)
        
        # Test basic discovery through session
        async with create_mcp_session(transport) as session:
            # Update tool manager to use session's protocol
            tool_manager.protocol = session.protocol
            
            # Discover tools
            tools = await tool_manager.discover_tools()
            logger.info(f"Discovered {len(tools)} tools: {list(tools.keys())}")
            
            # Test cache
            tools_cached = await tool_manager.discover_tools()
            assert tools == tools_cached
            logger.info("Tool caching working correctly")
            
            # Test tool info
            if tools:
                first_tool = list(tools.keys())[0]
                tool_info = await tool_manager.get_tool_info(first_tool)
                logger.info(f"Tool '{first_tool}' info: {json.dumps(tool_info, indent=2)}")
                
                # Test schema if available
                schema = await tool_manager.get_tool_schema(first_tool)
                if schema:
                    logger.info(f"Tool '{first_tool}' schema: {json.dumps(schema, indent=2)}")
                else:
                    logger.info(f"Tool '{first_tool}' has no schema")
            
            return tools
            
    except Exception as e:
        logger.error(f"Tool discovery test failed: {e}")
        return None


async def test_tool_execution():
    """Test tool execution functionality."""
    logger.info("Testing tool execution...")
    
    try:
        # Create transport and tool manager
        transport = StreamingTransport("http://localhost:8811")
        
        async with create_mcp_session(transport) as session:
            tool_manager = MCPToolManager(session.protocol, cache_ttl=60)
            
            # Discover tools first
            tools = await tool_manager.discover_tools()
            if not tools:
                logger.warning("No tools available for execution test")
                return
            
            # Test DuckDuckGo search if available
            if "duckduckgo_search" in tools:
                logger.info("Testing duckduckgo_search tool...")
                
                try:
                    # Test argument validation first
                    is_valid = await tool_manager.validate_tool_arguments(
                        "duckduckgo_search", 
                        {"query": "Python programming"}
                    )
                    logger.info(f"Argument validation result: {is_valid}")
                    
                    # Execute the tool
                    result = await tool_manager.execute_tool(
                        "duckduckgo_search",
                        {"query": "Python programming"}
                    )
                    
                    logger.info(f"Tool execution success: {result['success']}")
                    logger.info(f"Content length: {len(result['content'])}")
                    if result['error']:
                        logger.error(f"Tool execution error: {result['error']}")
                    else:
                        # Show first 200 characters of content
                        content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                        logger.info(f"Result preview: {content_preview}")
                    
                except Exception as e:
                    logger.error(f"Error executing duckduckgo_search: {e}")
                    
            # Test LinkedIn search if available
            if "linkedin_search" in tools:
                logger.info("Testing linkedin_search tool...")
                
                try:
                    result = await tool_manager.execute_tool(
                        "linkedin_search",
                        {"keywords": "Python developer", "location": "San Francisco"}
                    )
                    
                    logger.info(f"LinkedIn search success: {result['success']}")
                    content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                    logger.info(f"Result preview: {content_preview}")
                    
                except Exception as e:
                    logger.error(f"Error executing linkedin_search: {e}")
            
            # Test unknown tool handling
            logger.info("Testing unknown tool handling...")
            try:
                await tool_manager.execute_tool("nonexistent_tool", {"arg": "value"})
                logger.error("Should have raised ToolExecutionError!")
            except Exception as e:
                logger.info(f"Correctly handled unknown tool: {type(e).__name__}: {e}")
                
    except Exception as e:
        logger.error(f"Tool execution test failed: {e}")


async def test_result_normalization():
    """Test result normalization functionality."""
    logger.info("Testing result normalization...")
    
    # Test success result
    success_result = {
        "content": [
            {"type": "text", "text": "This is a successful result"},
            {"type": "text", "text": "With multiple parts"}
        ],
        "isError": False
    }
    
    normalized = ResultNormalizer.normalize_result(success_result)
    assert normalized["success"] is True
    assert "This is a successful result\nWith multiple parts" == normalized["content"]
    assert normalized["error"] is None
    logger.info("Success result normalization: PASSED")
    
    # Test error result
    error_result = {
        "content": [
            {"type": "text", "text": "Something went wrong"}
        ],
        "isError": True
    }
    
    normalized = ResultNormalizer.normalize_result(error_result)
    assert normalized["success"] is False
    assert normalized["error"] == "Something went wrong"
    logger.info("Error result normalization: PASSED")
    
    # Test create helper functions
    custom_error = ResultNormalizer.create_error_result("Custom error", "test_tool")
    assert custom_error["success"] is False
    assert custom_error["metadata"]["tool_name"] == "test_tool"
    logger.info("Custom error creation: PASSED")
    
    custom_success = ResultNormalizer.create_success_result("Custom success")
    assert custom_success["success"] is True
    assert custom_success["content"] == "Custom success"
    logger.info("Custom success creation: PASSED")


async def test_discovery_service():
    """Test tool discovery service functionality."""
    logger.info("Testing tool discovery service...")
    
    try:
        # Create discovery service
        discovery_service = ToolDiscoveryService()
        
        # Create multiple managers
        transport1 = StreamingTransport("http://localhost:8811")
        transport2 = StreamingTransport("http://localhost:8811")
        
        async with create_mcp_session(transport1) as session1:
            async with create_mcp_session(transport2) as session2:
                manager1 = MCPToolManager(session1.protocol, cache_ttl=60)
                manager2 = MCPToolManager(session2.protocol, cache_ttl=60)
                
                # Register managers
                discovery_service.register_manager("gateway1", manager1)
                discovery_service.register_manager("gateway2", manager2)
                
                # Discover all tools
                all_tools = await discovery_service.discover_all_tools()
                logger.info(f"Discovery service found tools from {len(all_tools)} managers")
                
                # Test finding tools
                if all_tools:
                    # Get first tool from any manager
                    for manager_name, tools in all_tools.items():
                        if tools:
                            tool_name = list(tools.keys())[0]
                            found_manager = await discovery_service.find_tool(tool_name)
                            if found_manager:
                                logger.info(f"Found tool '{tool_name}' in manager")
                                break
                
                # Test manager info
                manager_info = discovery_service.get_manager_info()
                logger.info(f"Manager info: {json.dumps(manager_info, indent=2)}")
                
    except Exception as e:
        logger.error(f"Discovery service test failed: {e}")


async def main():
    """Main test function."""
    logger.info("Starting Phase 3 Integration Tests")
    
    # Test 1: Gateway health
    if not await test_gateway_health():
        logger.error("Gateway is not available - please start the MCP gateway first")
        logger.info("Run: python mcp_gateway.py --port 8811")
        return
    
    # Test 2: Tool discovery
    tools = await test_tool_discovery()
    if not tools:
        logger.error("Tool discovery failed")
        return
    
    # Test 3: Tool execution
    await test_tool_execution()
    
    # Test 4: Result normalization
    await test_result_normalization()
    
    # Test 5: Discovery service
    await test_discovery_service()
    
    logger.info("All Phase 3 integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())