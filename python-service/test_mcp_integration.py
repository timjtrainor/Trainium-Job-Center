#!/usr/bin/env python3
"""
Test script for MCP Gateway integration with CrewAI.

This script tests the MCP Gateway connectivity and tool loading
to ensure the integration works properly.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.mcp_adapter import MCPServerAdapter, get_mcp_adapter
from app.services.crewai import base
from langchain.tools import BaseTool
from app.core.config import get_settings
from loguru import logger


async def test_mcp_gateway_connection():
    """Test basic MCP Gateway connection."""
    logger.info("Testing MCP Gateway connection...")
    
    settings = get_settings()
    gateway_url = settings.mcp_gateway_url
    
    try:
        async with get_mcp_adapter(gateway_url) as adapter:
            tools = adapter.get_available_tools()
            logger.info(f"Connected successfully! Available tools: {list(tools.keys())}")
            
            # Test DuckDuckGo tools specifically
            duckduckgo_tools = adapter.get_duckduckgo_tools()
            logger.info(f"DuckDuckGo tools: {len(duckduckgo_tools)}")
            
            for tool in duckduckgo_tools:
                logger.info(f"  - {tool.get('name')}: {tool.get('description')}")
                
            # Test tool execution
            if duckduckgo_tools:
                test_tool = duckduckgo_tools[0]
                logger.info(f"Testing tool execution: {test_tool['name']}")
                
                result = await adapter.call_tool(
                    test_tool['name'], 
                    query="Python programming",
                    max_results=3
                )
                logger.info(f"Tool execution result: {result[:200]}...")
                
        return True
        
    except Exception as e:
        logger.error(f"MCP Gateway test failed: {e}")
        return False


def test_crewai_tool_loading():
    """Test CrewAI tool loading through base utilities."""
    logger.info("Testing CrewAI tool loading...")
    
    try:
        # Test sync tool loading
        tools = base.load_mcp_tools_sync(["web_search"])
        logger.info(f"Loaded {len(tools)} tools through sync loader")

        for tool in tools:
            assert isinstance(tool, BaseTool)
            logger.info(f"  - {tool.name}: {tool.description}")
            
        # Test DuckDuckGo specific loading
        duckduckgo_tools = base.get_duckduckgo_tools()
        logger.info(f"DuckDuckGo tools from base loader: {len(duckduckgo_tools)}")
        
        return len(tools) > 0 or len(duckduckgo_tools) > 0
        
    except Exception as e:
        logger.error(f"CrewAI tool loading test failed: {e}")
        return False


async def test_job_review_crew_integration():
    """Test JobReviewCrew with MCP tools."""
    logger.info("Testing JobReviewCrew integration...")
    
    try:
        from app.services.crewai.job_review.crew import JobReviewCrew
        
        # Create crew instance
        crew = JobReviewCrew()
        
        # Test preparation (this should load MCP tools)
        test_inputs = {
            "job": {
                "title": "Senior Python Developer",
                "company": "Test Company",
                "description": "Looking for experienced Python developer with CrewAI experience"
            }
        }
        
        # This will trigger MCP tool loading in prepare_analysis
        prepared_inputs = crew.prepare_analysis(test_inputs)
        
        mcp_tools = prepared_inputs.get("mcp_tools", [])
        logger.info(f"JobReviewCrew loaded {len(mcp_tools)} MCP tools")

        for tool in mcp_tools:
            logger.info(f"  - {tool.name}: {getattr(tool, 'description', 'No description')}")
            
        return len(mcp_tools) > 0
        
    except Exception as e:
        logger.error(f"JobReviewCrew integration test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    logger.info("Starting MCP Gateway integration tests...")
    
    # Configure logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:HH:mm:ss} | {level} | {message}",
        level="INFO",
        colorize=True
    )
    
    tests = [
        ("MCP Gateway Connection", test_mcp_gateway_connection),
        ("CrewAI Tool Loading", lambda: test_crewai_tool_loading()),
        ("JobReviewCrew Integration", test_job_review_crew_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            logger.info(f"Test {test_name}: {status}")
            
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("Test Summary")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests passed! 🎉")
        return 0
    else:
        logger.error("Some tests failed! ❌")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())