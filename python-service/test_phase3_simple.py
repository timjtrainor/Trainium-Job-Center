#!/usr/bin/env python3
"""
Simple Phase 3 Test - Direct HTTP calls to MCP Gateway

This script tests the new Phase 3 functionality by making direct HTTP calls
to the MCP gateway endpoints to validate tool discovery and execution.
"""

import asyncio
import json
import logging
import httpx
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our result normalizer
from app.services.mcp.mcp_results import ResultNormalizer


async def test_direct_tool_discovery():
    """Test tool discovery via direct HTTP calls."""
    logger.info("Testing tool discovery via HTTP...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test tools/list endpoint
            tools_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            response = await client.post(
                "http://localhost:8811/mcp/tools/list",
                json=tools_request,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Tools discovery response: {json.dumps(result, indent=2)}")
                
                if "result" in result and "tools" in result["result"]:
                    tools = result["result"]["tools"]
                    logger.info(f"Found {len(tools)} tools:")
                    for tool in tools:
                        logger.info(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                    return tools
                else:
                    logger.error("Invalid tools response format")
                    return []
            else:
                logger.error(f"Tools discovery failed: {response.status_code} - {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Tool discovery test failed: {e}")
        return []


async def test_direct_tool_execution():
    """Test tool execution via direct HTTP calls."""
    logger.info("Testing tool execution via HTTP...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test duckduckgo_search tool
            tool_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "duckduckgo_search",
                    "arguments": {
                        "query": "Python programming"
                    }
                }
            }
            
            response = await client.post(
                "http://localhost:8811/mcp/tools/call",
                json=tool_request,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Tool execution response: {json.dumps(result, indent=2)}")
                
                if "result" in result:
                    # Test result normalization
                    normalized = ResultNormalizer.normalize_result(result["result"])
                    logger.info(f"Normalized result success: {normalized['success']}")
                    logger.info(f"Content length: {len(normalized['content'])}")
                    
                    if normalized["content"]:
                        preview = normalized["content"][:200] + "..." if len(normalized["content"]) > 200 else normalized["content"]
                        logger.info(f"Content preview: {preview}")
                    
                    if normalized["error"]:
                        logger.error(f"Tool error: {normalized['error']}")
                    
                    return normalized
                else:
                    logger.error("Invalid tool execution response format")
                    return None
            else:
                logger.error(f"Tool execution failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Tool execution test failed: {e}")
        return None


async def test_unknown_tool():
    """Test execution of unknown tool."""
    logger.info("Testing unknown tool handling...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test unknown tool
            tool_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "nonexistent_tool",
                    "arguments": {}
                }
            }
            
            response = await client.post(
                "http://localhost:8811/mcp/tools/call",
                json=tool_request,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Unknown tool response: {json.dumps(result, indent=2)}")
                
                if "error" in result:
                    logger.info(f"Correctly handled unknown tool with error: {result['error']['message']}")
                else:
                    logger.warning("Expected error response for unknown tool")
                    
            else:
                logger.info(f"Unknown tool correctly rejected with status: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Unknown tool test failed: {e}")


async def test_result_normalization_functions():
    """Test result normalization utility functions."""
    logger.info("Testing result normalization functions...")
    
    # Test success result creation
    success_result = ResultNormalizer.create_success_result("Test success message")
    assert success_result["success"] is True
    assert success_result["content"] == "Test success message"
    logger.info("✓ Success result creation works")
    
    # Test error result creation
    error_result = ResultNormalizer.create_error_result("Test error message", "test_tool")
    assert error_result["success"] is False
    assert error_result["error"] == "Test error message"
    assert error_result["metadata"]["tool_name"] == "test_tool"
    logger.info("✓ Error result creation works")
    
    # Test response validation
    valid_response = {
        "content": [{"type": "text", "text": "Valid response"}],
        "isError": False
    }
    assert ResultNormalizer.validate_tool_response(valid_response) is True
    logger.info("✓ Response validation works")
    
    invalid_response = {"not_content": "invalid"}
    assert ResultNormalizer.validate_tool_response(invalid_response) is False
    logger.info("✓ Invalid response detection works")
    
    # Test text extraction
    multi_content = {
        "content": [
            {"type": "text", "text": "Part 1"},
            {"type": "text", "text": "Part 2"},
            {"type": "resource", "resource": {"text": "Resource text"}}
        ]
    }
    extracted_text = ResultNormalizer.extract_text_content(multi_content)
    assert "Part 1\nPart 2\nResource text" == extracted_text
    logger.info("✓ Text extraction works")
    
    logger.info("All result normalization functions work correctly!")


async def main():
    """Main test function."""
    logger.info("Starting Simple Phase 3 Integration Tests")
    
    # Test 1: Tool discovery
    tools = await test_direct_tool_discovery()
    if not tools:
        logger.error("Tool discovery failed - stopping tests")
        return
    
    # Test 2: Tool execution
    result = await test_direct_tool_execution()
    if result is None:
        logger.error("Tool execution test failed")
        return
    
    # Test 3: Unknown tool handling
    await test_unknown_tool()
    
    # Test 4: Result normalization functions
    await test_result_normalization_functions()
    
    logger.info("All simple integration tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())