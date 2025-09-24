#!/usr/bin/env python3
"""
Phase 3 Demo - Tool Discovery and Execution

This script demonstrates the new Phase 3 MCP functionality for tool discovery
and execution. It shows how to use the MCPToolManager and related classes.
"""

import asyncio
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Import MCP Phase 3 modules
from app.services.mcp import (
    MCPToolManager, ToolDiscoveryService, ResultNormalizer,
    MCPProtocol, StreamingTransport, create_mcp_session,
    ToolExecutionError, ProtocolError
)


async def demo_basic_tool_usage():
    """Demonstrate basic tool discovery and execution."""
    logger.info("=== Phase 3 Demo: Basic Tool Usage ===")
    
    try:
        # Create transport - in a real implementation, this would connect to actual MCP servers
        # For demo, we'll use a placeholder transport
        logger.info("Note: This demo uses placeholder transport - for real usage, configure actual MCP servers")
        
        # The basic usage pattern would be:
        # transport = StreamingTransport("http://mcp-gateway:8811")
        # async with create_mcp_session(transport) as session:
        #     tool_manager = MCPToolManager(session.protocol, cache_ttl=300)
        #     ... use tool_manager ...
        
        logger.info("Basic usage pattern:")
        logger.info("1. Create transport connection to MCP gateway")
        logger.info("2. Create MCP session with protocol handling")
        logger.info("3. Create MCPToolManager for tool operations")
        logger.info("4. Discover and execute tools as needed")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")


async def demo_result_normalization():
    """Demonstrate result normalization capabilities."""
    logger.info("\n=== Phase 3 Demo: Result Normalization ===")
    
    # Example raw MCP tool response
    raw_success_response = {
        "content": [
            {"type": "text", "text": "Search found 10 results"},
            {"type": "text", "text": "Top result: Python.org - The official Python website"}
        ],
        "isError": False
    }
    
    # Normalize the response
    normalized = ResultNormalizer.normalize_result(raw_success_response)
    
    logger.info("Raw MCP response:")
    logger.info(json.dumps(raw_success_response, indent=2))
    
    logger.info("\nNormalized result:")
    logger.info(f"  Success: {normalized['success']}")
    logger.info(f"  Content: {normalized['content']}")
    logger.info(f"  Error: {normalized['error']}")
    logger.info(f"  Metadata: {json.dumps(normalized['metadata'], indent=4)}")
    
    # Example error response
    raw_error_response = {
        "content": [
            {"type": "text", "text": "Tool execution failed: invalid query parameter"}
        ],
        "isError": True
    }
    
    normalized_error = ResultNormalizer.normalize_result(raw_error_response)
    
    logger.info("\nError response normalization:")
    logger.info(f"  Success: {normalized_error['success']}")
    logger.info(f"  Error: {normalized_error['error']}")
    
    # Demonstrate helper functions
    logger.info("\nResult creation helpers:")
    
    custom_success = ResultNormalizer.create_success_result("Custom success message")
    logger.info(f"  Created success: {custom_success['success']} - {custom_success['content']}")
    
    custom_error = ResultNormalizer.create_error_result("Custom error", "demo_tool")
    logger.info(f"  Created error: {custom_error['success']} - {custom_error['error']}")


async def demo_tool_manager_features():
    """Demonstrate MCPToolManager features without actual connections."""
    logger.info("\n=== Phase 3 Demo: Tool Manager Features ===")
    
    logger.info("MCPToolManager provides:")
    logger.info("✓ Tool discovery with caching (configurable TTL)")
    logger.info("✓ Tool execution with argument validation")
    logger.info("✓ Result normalization")
    logger.info("✓ Error handling for unknown tools")
    logger.info("✓ JSON Schema validation for tool arguments")
    
    logger.info("\nKey methods:")
    logger.info("  await tool_manager.discover_tools() -> Dict[str, Dict]")
    logger.info("  await tool_manager.get_tool_info(name) -> Dict")
    logger.info("  await tool_manager.execute_tool(name, args) -> Dict")
    logger.info("  await tool_manager.validate_tool_arguments(name, args) -> bool")
    logger.info("  tool_manager.list_tool_names() -> List[str]")
    logger.info("  tool_manager.clear_cache() -> None")
    
    # Demonstrate cache info
    logger.info("\nCache management:")
    logger.info("  Cache TTL: Configurable (default 5 minutes)")
    logger.info("  Cache info available via tool_manager.cache_info property")
    logger.info("  Thread-safe cache operations with asyncio locks")


async def demo_discovery_service():
    """Demonstrate ToolDiscoveryService for managing multiple tool sources."""
    logger.info("\n=== Phase 3 Demo: Discovery Service ===")
    
    logger.info("ToolDiscoveryService enables:")
    logger.info("✓ Managing multiple MCP tool managers")
    logger.info("✓ Discovering tools across all registered managers")
    logger.info("✓ Finding which manager provides a specific tool")
    logger.info("✓ Executing tools from any available manager")
    
    # Create example service
    discovery_service = ToolDiscoveryService()
    
    logger.info("\nExample usage:")
    logger.info("  service = ToolDiscoveryService()")
    logger.info("  service.register_manager('gateway1', manager1)")
    logger.info("  service.register_manager('gateway2', manager2)")
    logger.info("  all_tools = await service.discover_all_tools()")
    logger.info("  manager = await service.find_tool('tool_name')")
    logger.info("  result = await service.execute_tool_anywhere('tool_name', args)")
    
    # Show manager registration
    logger.info(f"\nCurrently registered managers: {len(discovery_service._managers)}")


async def demo_error_handling():
    """Demonstrate error handling patterns."""
    logger.info("\n=== Phase 3 Demo: Error Handling ===")
    
    logger.info("Phase 3 provides specific exception types:")
    logger.info("✓ ToolExecutionError - for tool-specific failures")
    logger.info("✓ ProtocolError - for MCP protocol violations")
    logger.info("✓ TimeoutError - for operation timeouts")
    logger.info("✓ ConnectionError - for transport failures")
    
    logger.info("\nError handling pattern:")
    code_example = '''
try:
    result = await tool_manager.execute_tool("search", {"query": "python"})
    if result["success"]:
        print(f"Result: {result['content']}")
    else:
        print(f"Tool reported error: {result['error']}")
        
except ToolExecutionError as e:
    print(f"Tool execution failed: {e}")
    print(f"Tool name: {e.tool_name}")
    print(f"Arguments: {e.arguments}")
    
except ProtocolError as e:
    print(f"Protocol error: {e}")
    
except Exception as e:
    print(f"Unexpected error: {e}")
'''
    logger.info(code_example)


async def demo_integration_patterns():
    """Demonstrate integration patterns for real applications."""
    logger.info("\n=== Phase 3 Demo: Integration Patterns ===")
    
    logger.info("Common integration patterns:")
    
    logger.info("\n1. Simple tool execution:")
    simple_pattern = '''
async with create_mcp_session(transport) as session:
    tool_manager = MCPToolManager(session.protocol)
    result = await tool_manager.execute_tool("search", {"query": "python"})
    return result["content"] if result["success"] else None
'''
    logger.info(simple_pattern)
    
    logger.info("2. Multi-source tool discovery:")
    multi_pattern = '''
discovery_service = ToolDiscoveryService()
discovery_service.register_manager("web_tools", web_manager)
discovery_service.register_manager("data_tools", data_manager)

# Find and execute any tool from any source
result = await discovery_service.execute_tool_anywhere("search", {"query": "test"})
'''
    logger.info(multi_pattern)
    
    logger.info("3. Cached tool operations:")
    cached_pattern = '''
# Long-lived tool manager with caching
tool_manager = MCPToolManager(protocol, cache_ttl=600)  # 10 minute cache

# First call discovers and caches tools
tools = await tool_manager.discover_tools()

# Subsequent calls use cache (much faster)
tool_info = await tool_manager.get_tool_info("search")  # Uses cache
result = await tool_manager.execute_tool("search", args)  # Always executes
'''
    logger.info(cached_pattern)


async def main():
    """Run all demos."""
    logger.info("Phase 3: Tool Discovery and Execution - Feature Demo")
    logger.info("=" * 60)
    
    await demo_basic_tool_usage()
    await demo_result_normalization()
    await demo_tool_manager_features()
    await demo_discovery_service()
    await demo_error_handling()
    await demo_integration_patterns()
    
    logger.info("\n" + "=" * 60)
    logger.info("Phase 3 implementation provides a complete tool management layer")
    logger.info("for MCP (Model Context Protocol) with caching, validation, and")
    logger.info("error handling. Ready for integration into larger applications!")


if __name__ == "__main__":
    asyncio.run(main())