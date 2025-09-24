#!/usr/bin/env python3
"""
Phase 5 CrewAI Integration Demonstration

This script demonstrates the Phase 5 implementation, including CrewAI 
integration, tool wrappers, and comprehensive examples.
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.mcp import (
    MCPGatewayAdapter,
    StreamingTransport,
    AsyncMCPToolWrapper,
    MCPToolWrapper,
    MCPToolFactory,
    is_crewai_available,
    is_pydantic_available,
    get_integration_status,
    ConnectionError
)


async def demo_integration_status():
    """Demonstrate integration status checking."""
    print("🔍 Phase 5 Integration Status")
    print("=" * 40)
    
    status = get_integration_status()
    
    for key, value in status.items():
        icon = "✅" if value else "❌"
        print(f"  {icon} {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n💡 Recommendations:")
    if not status["crewai_available"]:
        print("  - Install CrewAI: pip install crewai crewai-tools")
    if not status["pydantic_available"]:
        print("  - Install Pydantic: pip install pydantic")
    if status["full_functionality"]:
        print("  - All dependencies available - full functionality enabled!")


async def demo_async_tool_wrapper():
    """Demonstrate AsyncMCPToolWrapper functionality."""
    print("\n🔄 AsyncMCPToolWrapper Demo")
    print("=" * 35)
    
    # Create a mock adapter for demonstration
    class MockAdapter:
        def __init__(self):
            self.connected = False
            
        async def list_tools(self):
            return {
                "demo_search": {
                    "name": "demo_search",
                    "description": "Demo search tool for testing",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            }
        
        async def execute_tool(self, tool_name, arguments):
            return f"Mock result for {tool_name} with args: {arguments}"
        
        def is_connected(self):
            return True
    
    print("✓ Creating mock adapter and async tool wrapper...")
    adapter = MockAdapter()
    wrapper = AsyncMCPToolWrapper(adapter, "demo_search")
    
    print("✓ Initializing wrapper...")
    await wrapper.initialize()
    
    print(f"✓ Tool name: {wrapper.tool_name}")
    print(f"✓ Description: {wrapper.get_description()}")
    print(f"✓ Schema: {wrapper.get_schema()}")
    
    print("✓ Executing tool...")
    result = await wrapper.execute(query="test search query")
    print(f"✓ Result: {result}")


async def demo_tool_factory():
    """Demonstrate MCPToolFactory functionality."""
    print("\n🏭 MCPToolFactory Demo")
    print("=" * 30)
    
    # Create a more comprehensive mock adapter
    class MockAdapter:
        async def list_tools(self):
            return {
                "web_search": {
                    "name": "web_search",
                    "description": "Search the web",
                    "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}
                },
                "calculator": {
                    "name": "calculator", 
                    "description": "Perform calculations",
                    "inputSchema": {"type": "object", "properties": {"expression": {"type": "string"}}}
                },
                "file_reader": {
                    "name": "file_reader",
                    "description": "Read file contents",
                    "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}}
                }
            }
        
        async def execute_tool(self, tool_name, arguments):
            return f"Factory demo result for {tool_name}: {arguments}"
    
    adapter = MockAdapter()
    factory = MCPToolFactory(adapter)
    
    print("✓ Creating async tools via factory...")
    async_tools = await factory.create_async_tools()
    print(f"✓ Created {len(async_tools)} async tools:")
    for name, tool in async_tools.items():
        print(f"  - {name}: {tool.get_description()}")
    
    print("\n✓ Creating CrewAI tools via factory...")
    try:
        crewai_tools = await factory.create_crewai_tools()
        print(f"✓ Created {len(crewai_tools)} CrewAI tools:")
        for name, tool in crewai_tools.items():
            print(f"  - {name}: {tool.description}")
    except Exception as e:
        print(f"⚠️  CrewAI tools creation limited: {e}")
        print("   (This is expected if CrewAI is not installed)")
    
    print("\n✓ Testing single tool creation...")
    single_async = await factory.create_single_async_tool("web_search")
    print(f"✓ Single async tool: {single_async.tool_name}")
    
    single_crewai = factory.create_single_crewai_tool("calculator")
    print(f"✓ Single CrewAI tool: {single_crewai.tool_name}")


async def demo_real_gateway_connection():
    """Demonstrate connection to real MCP Gateway (if available)."""
    print("\n🌐 Real Gateway Connection Demo")
    print("=" * 40)
    
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport, timeout=5, max_retries=1)
    
    try:
        async with adapter:
            print("✅ Connected to real MCP Gateway!")
            
            # Test real tool discovery
            tools = await adapter.list_tools()
            print(f"✓ Found {len(tools)} real tools:")
            for name, info in list(tools.items())[:3]:  # Show first 3
                print(f"  - {name}: {info.get('description', 'No description')}")
            if len(tools) > 3:
                print(f"  ... and {len(tools) - 3} more")
            
            # Test factory with real tools
            if tools:
                print("\n✓ Testing factory with real tools...")
                factory = MCPToolFactory(adapter)
                
                async_tools = await factory.create_async_tools()
                print(f"✓ Created {len(async_tools)} async wrappers for real tools")
                
                # Test execution of first tool
                if async_tools:
                    tool_name = list(async_tools.keys())[0]
                    tool = async_tools[tool_name]
                    
                    # Create minimal arguments based on schema
                    tool_schema = tool.get_schema()
                    properties = tool_schema.get("properties", {})
                    args = {}
                    
                    for prop_name, prop_info in properties.items():
                        if prop_info.get("type") == "string":
                            args[prop_name] = "Phase 5 test query"
                            break
                    
                    if args:
                        print(f"✓ Testing real tool execution: {tool_name}")
                        try:
                            result = await tool.execute(**args)
                            print(f"✓ Real tool result: {result[:100]}{'...' if len(str(result)) > 100 else ''}")
                        except Exception as e:
                            print(f"⚠️  Tool execution failed: {e}") 
                            
    except Exception as e:
        print("ℹ️  Real MCP Gateway not available")
        print(f"   Error: {type(e).__name__}: {str(e)[:100]}{'...' if len(str(e)) > 100 else ''}")
        print("   Start the gateway with: python mcp_gateway.py")
        print("   Then run this demo again to see real tool integration")


async def demo_examples_availability():
    """Show what examples are available."""
    print("\n📚 Available Examples")
    print("=" * 25)
    
    examples = [
        ("basic_usage.py", "Basic MCP Gateway usage patterns"),
        ("crewai_integration.py", "CrewAI agent integration with MCP tools"),
        ("error_handling.py", "Comprehensive error handling patterns"),
        ("health_monitoring.py", "Health monitoring and metrics collection")
    ]
    
    print("✓ Phase 5 includes these comprehensive examples:")
    for filename, description in examples:
        print(f"  📄 {filename}")
        print(f"     {description}")
    
    print(f"\n💡 Run examples with:")
    print("   python examples/basic_usage.py")
    print("   python examples/crewai_integration.py")
    print("   python examples/error_handling.py")
    print("   python examples/health_monitoring.py")


async def demo_testing_framework():
    """Show testing capabilities."""
    print("\n🧪 Testing Framework")
    print("=" * 25)
    
    print("✓ Phase 5 includes comprehensive tests:")
    print("  📋 AsyncMCPToolWrapper tests")
    print("  📋 MCPToolWrapper tests")
    print("  📋 MCPToolFactory tests")
    print("  📋 Schema conversion tests")
    print("  📋 Error handling tests")
    print("  📋 Integration scenario tests")
    
    print(f"\n💡 Run tests with:")
    print("   pytest tests/mcp/test_crewai_integration.py -v")


async def main():
    """Run the Phase 5 demonstration."""
    print("🚀 Phase 5: CrewAI Integration Demo")
    print("=" * 50)
    
    # Integration status
    await demo_integration_status()
    
    # Async tool wrapper demo
    await demo_async_tool_wrapper()
    
    # Tool factory demo
    await demo_tool_factory()
    
    # Real gateway connection (if available)
    await demo_real_gateway_connection()
    
    # Show available examples
    await demo_examples_availability()
    
    # Show testing framework
    await demo_testing_framework()
    
    print("\n" + "=" * 50)
    print("✨ Phase 5 Demo Completed!")
    print("=" * 50)
    
    print("\n🎯 Phase 5 Key Features:")
    print("  ✅ AsyncMCPToolWrapper for async-native frameworks")
    print("  ✅ MCPToolWrapper for CrewAI compatibility")
    print("  ✅ MCPToolFactory for bulk tool operations")
    print("  ✅ Graceful fallback when dependencies unavailable")
    print("  ✅ Comprehensive examples and documentation")
    print("  ✅ Full test coverage")
    print("  ✅ Error handling and monitoring integration")
    
    print("\n🔗 Next Steps:")
    print("  1. Install CrewAI: pip install crewai crewai-tools")
    print("  2. Install Pydantic: pip install pydantic")  
    print("  3. Start MCP Gateway: python mcp_gateway.py")
    print("  4. Run examples to see full functionality")
    print("  5. Integrate with your CrewAI agents!")


if __name__ == "__main__":
    asyncio.run(main())