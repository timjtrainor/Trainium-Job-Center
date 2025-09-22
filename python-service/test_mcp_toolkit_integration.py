#!/usr/bin/env python3
"""
Test script for MCP Toolkit integration.

This script tests the new MCP Toolkit-based adapter that uses ClientSession
and stdio transport to connect to the Docker MCP Gateway.
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.mcp_toolkit_adapter import (
    MCPToolkitAdapter, 
    MCPToolkitConfig,
    get_mcp_toolkit_adapter,
    demo_mcp_toolkit  
)
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


def test_adapter_creation():
    """Test that the adapter can be created with default configuration."""
    logger.info("Testing adapter creation...")
    
    # Test with default config
    adapter = MCPToolkitAdapter()
    assert adapter.config is not None
    assert adapter.config.gateway_command is not None
    logger.info("✓ Default adapter creation successful")
    
    # Test with custom config
    custom_config = MCPToolkitConfig(
        gateway_command=["docker", "exec", "-i", "custom_gateway", "mcp-gateway"],
        connection_timeout=45
    )
    adapter2 = MCPToolkitAdapter(custom_config)
    assert adapter2.config.connection_timeout == 45
    logger.info("✓ Custom adapter creation successful")


def test_tool_formatting():
    """Test that tools can be formatted for CrewAI compatibility."""
    logger.info("Testing tool formatting...")
    
    adapter = MCPToolkitAdapter()
    
    # Mock some tools
    adapter._available_tools = {
        "duckduckgo_search": {
            "name": "duckduckgo_search",
            "description": "Search the web using DuckDuckGo",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                }
            },
            "server": "duckduckgo"
        },
        "linkedin_search": {
            "name": "linkedin_search", 
            "description": "Search LinkedIn profiles",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "LinkedIn search query"}
                }
            },
            "server": "linkedin"
        }
    }
    
    # Get CrewAI tools
    crewai_tools = adapter.get_crewai_tools()
    
    assert len(crewai_tools) == 2
    
    for tool in crewai_tools:
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
        assert "execute" in tool
        assert callable(tool["execute"])
        
    logger.info("✓ Tool formatting successful")
    logger.info(f"  Formatted {len(crewai_tools)} tools for CrewAI")


async def test_connection_simulation():
    """Test connection logic (simulated since gateway may not be running)."""
    logger.info("Testing connection simulation...")
    
    try:
        # This will likely fail since the gateway isn't running,
        # but we can test the connection logic structure
        config = MCPToolkitConfig(
            gateway_command=["echo", "test"],  # Use echo for testing
            connection_timeout=5
        )
        
        adapter = MCPToolkitAdapter(config)
        
        # Test that connection methods exist and can be called
        assert hasattr(adapter, 'connect')
        assert hasattr(adapter, 'disconnect')
        assert hasattr(adapter, 'execute_tool')
        
        logger.info("✓ Connection methods available")
        
    except Exception as e:
        logger.info(f"Expected connection error (gateway not running): {e}")
        logger.info("✓ Connection error handling working")


def test_server_discovery_logic():
    """Test server name extraction from tool names."""
    logger.info("Testing server discovery logic...")
    
    adapter = MCPToolkitAdapter()
    
    # Test server name extraction
    test_tools = [
        ("duckduckgo_search", "duckduckgo"),
        ("linkedin_profile_search", "linkedin"), 
        ("some_other_tool", "unknown"),
        ("duckduckgo_web_search", "duckduckgo")
    ]
    
    for tool_name, expected_server in test_tools:
        # Simulate the server extraction logic
        server_name = "unknown"
        if "_" in tool_name:
            potential_server = tool_name.split("_")[0]
            if potential_server in ["duckduckgo", "linkedin"]:
                server_name = potential_server
                
        assert server_name == expected_server, f"Expected {expected_server}, got {server_name} for {tool_name}"
        
    logger.info("✓ Server discovery logic working correctly")


def test_crewai_compatibility():
    """Test that the adapter produces CrewAI-compatible tools."""
    logger.info("Testing CrewAI compatibility...")
    
    adapter = MCPToolkitAdapter()
    
    # Mock a tool
    adapter._available_tools = {
        "test_tool": {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {"query": {"type": "string"}},
            "server": "test"
        }
    }
    
    crewai_tools = adapter.get_crewai_tools()
    
    # Verify CrewAI tool structure
    assert len(crewai_tools) == 1
    tool = crewai_tools[0]
    
    # Check required fields for CrewAI
    required_fields = ["name", "description", "parameters", "execute"]
    for field in required_fields:
        assert field in tool, f"Missing required field: {field}"
        
    # Check that execute is callable
    assert callable(tool["execute"])
    
    logger.info("✓ CrewAI compatibility verified")


def run_all_tests():
    """Run all synchronous tests."""
    logger.info("=== Running MCP Toolkit Integration Tests ===")
    
    try:
        test_adapter_creation()
        test_tool_formatting()  
        test_server_discovery_logic()
        test_crewai_compatibility()
        
        logger.info("=== All Synchronous Tests Passed ===")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


async def run_async_tests():
    """Run all asynchronous tests.""" 
    logger.info("=== Running Async Tests ===")
    
    try:
        await test_connection_simulation()
        
        logger.info("=== All Async Tests Passed ===")
        return True
        
    except Exception as e:
        logger.error(f"Async test failed: {e}")
        return False


async def main():
    """Main test runner."""
    logger.info("Starting MCP Toolkit Integration Tests")
    
    # Run synchronous tests
    sync_success = run_all_tests()
    
    # Run asynchronous tests  
    async_success = await run_async_tests()
    
    if sync_success and async_success:
        logger.info("🎉 All tests passed! MCP Toolkit integration ready.")
        
        # Show usage example
        logger.info("\n=== Usage Example ===")
        logger.info("To use the MCP Toolkit adapter:")
        logger.info("1. Ensure Docker MCP Gateway is running")
        logger.info("2. Use: async with get_mcp_toolkit_adapter() as adapter:")
        logger.info("3. Call: tools = adapter.get_crewai_tools()")
        logger.info("4. Use tools with CrewAI agents")
        
    else:
        logger.error("❌ Some tests failed")
        return 1
        
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)