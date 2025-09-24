#!/usr/bin/env python3
"""Error Handling Example.

This example demonstrates comprehensive error handling patterns for MCP 
Gateway integration, including:
- Connection failures and retries
- Tool execution errors
- Timeout handling
- Resource cleanup
- Graceful degradation strategies
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.mcp import (
    MCPGatewayAdapter,
    MCPConfig,
    StreamingTransport,
    StdioTransport,
    MCPError,
    ConnectionError,
    HandshakeError,
    TransportError,
    ProtocolError,
    TimeoutError,
    ToolExecutionError,
    ConfigurationError,
    MCPToolFactory,
    AsyncMCPToolWrapper
)


async def connection_error_handling():
    """Demonstrate connection error handling patterns."""
    print("🔌 Connection Error Handling")
    print("=" * 35)
    
    # Example 1: Invalid gateway URL
    print("\n1. Invalid Gateway URL")
    transport = StreamingTransport("http://invalid-gateway:9999")
    adapter = MCPGatewayAdapter(
        transport=transport,
        timeout=5,  # Short timeout for demo
        max_retries=2
    )
    
    try:
        async with adapter:
            await adapter.list_tools()
        print("❌ Unexpected success - should have failed!")
    except ConnectionError as e:
        print(f"✓ Correctly caught ConnectionError: {e}")
    except Exception as e:
        print(f"✓ Caught unexpected error: {type(e).__name__}: {e}")
    
    # Example 2: Connection timeout
    print("\n2. Connection Timeout")
    transport = StreamingTransport("http://192.0.2.1:8811")  # Non-routable IP
    adapter = MCPGatewayAdapter(transport=transport, timeout=3, max_retries=1)
    
    try:
        async with adapter:
            await adapter.list_tools()
        print("❌ Unexpected success - should have timed out!")
    except (ConnectionError, TimeoutError) as e:
        print(f"✓ Correctly caught timeout/connection error: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"✓ Caught error: {type(e).__name__}: {e}")
    
    # Example 3: Retry mechanism demonstration
    print("\n3. Retry Mechanism")
    class FailingTransport(StreamingTransport):
        def __init__(self, fail_count=2):
            super().__init__("http://localhost:8811")
            self.fail_count = fail_count
            self.attempt_count = 0
            
        async def send_request(self, request):
            self.attempt_count += 1
            if self.attempt_count <= self.fail_count:
                raise ConnectionError(f"Simulated failure #{self.attempt_count}")
            return await super().send_request(request)
    
    failing_transport = FailingTransport(fail_count=2)
    adapter = MCPGatewayAdapter(
        transport=failing_transport,
        timeout=10,
        max_retries=3
    )
    
    try:
        print("   Attempting connection with simulated failures...")
        async with adapter:
            print("✓ Connection successful after retries!")
    except ConnectionError as e:
        print(f"✓ Connection failed after all retries: {e}")
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")


async def tool_execution_error_handling():
    """Demonstrate tool execution error patterns."""
    print("\n🛠️  Tool Execution Error Handling")
    print("=" * 40)
    
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    
    try:
        async with adapter:
            print("✓ Connected for tool error testing")
            
            # Example 1: Non-existent tool
            print("\n1. Non-existent Tool Execution")
            try:
                result = await adapter.execute_tool("nonexistent_tool", {"param": "value"})
                print("❌ Unexpected success - tool should not exist!")
            except ToolExecutionError as e:
                print(f"✓ Correctly caught ToolExecutionError: {e}")
            except Exception as e:
                print(f"✓ Caught error: {type(e).__name__}: {e}")
            
            # Example 2: Invalid tool parameters
            print("\n2. Invalid Tool Parameters")
            tools = await adapter.list_tools()
            if tools:
                tool_name = list(tools.keys())[0]
                try:
                    # Intentionally invalid parameters
                    result = await adapter.execute_tool(tool_name, {"invalid_param": "value"})
                    print(f"⚠️  Tool executed despite invalid params: {result[:100]}...")
                except ToolExecutionError as e:
                    print(f"✓ Correctly caught parameter error: {e}")
                except Exception as e:
                    print(f"✓ Caught error: {type(e).__name__}: {e}")
            else:
                print("ℹ️  No tools available for parameter testing")
            
            # Example 3: Tool timeout (simulated)
            print("\n3. Tool Execution Timeout")
            if tools:
                tool_name = list(tools.keys())[0]
                
                # Create a wrapper that simulates timeout
                class TimeoutingAdapter(MCPGatewayAdapter):
                    async def execute_tool(self, tool_name, arguments):
                        await asyncio.sleep(0.1)  # Simulate slow execution
                        raise TimeoutError("Simulated tool timeout")
                
                timeout_adapter = TimeoutingAdapter(transport=transport)
                try:
                    result = await timeout_adapter.execute_tool(tool_name, {})
                    print("❌ Unexpected success - should have timed out!")
                except TimeoutError as e:
                    print(f"✓ Correctly caught TimeoutError: {e}")
                except Exception as e:
                    print(f"✓ Caught error: {type(e).__name__}: {e}")
    
    except ConnectionError:
        print("ℹ️  Gateway not available - skipping tool execution error tests")


async def resource_cleanup_patterns():
    """Demonstrate proper resource cleanup patterns."""
    print("\n🧹 Resource Cleanup Patterns")
    print("=" * 35)
    
    # Example 1: Context manager cleanup
    print("\n1. Automatic Cleanup with Context Manager")
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    
    try:
        async with adapter:  # Automatic cleanup guaranteed
            print("✓ Inside context manager - resources acquired")
            tools = await adapter.list_tools() 
            print(f"✓ Found {len(tools)} tools")
            # Exception here would still trigger cleanup
            
        print("✓ Context manager exited - resources cleaned up")
        
    except ConnectionError:
        print("ℹ️  Gateway not available - cleanup still occurred")
    
    # Example 2: Manual cleanup in exception handler
    print("\n2. Manual Cleanup in Exception Handler")
    adapter2 = MCPGatewayAdapter(transport=StreamingTransport("http://localhost:8811"))
    
    try:
        await adapter2.connect()
        print("✓ Manual connection successful")
        
        # Simulate some work
        try:
            await adapter2.list_tools()
        except Exception as e:
            print(f"⚠️  Operation failed: {e}")
        
    except ConnectionError:
        print("ℹ️  Connection failed")
    finally:
        # Ensure cleanup happens
        await adapter2.disconnect()
        print("✓ Manual cleanup completed")
    
    # Example 3: Multiple adapter cleanup
    print("\n3. Multiple Adapter Cleanup")
    adapters = []
    
    try:
        # Create multiple adapters
        for i in range(3):
            adapter = MCPGatewayAdapter(
                transport=StreamingTransport(f"http://localhost:881{i}"),
                timeout=2
            )
            adapters.append(adapter)
        
        print(f"✓ Created {len(adapters)} adapters")
        
        # Try to connect all (some may fail)
        for i, adapter in enumerate(adapters):
            try:
                await adapter.connect()
                print(f"✓ Adapter {i} connected")
            except ConnectionError:
                print(f"ℹ️  Adapter {i} connection failed")
    
    finally:
        # Cleanup all adapters
        print("🧹 Cleaning up all adapters...")
        cleanup_tasks = [adapter.disconnect() for adapter in adapters]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        print("✓ All adapters cleaned up")


async def graceful_degradation_patterns():
    """Demonstrate graceful degradation when MCP is unavailable."""
    print("\n🔄 Graceful Degradation Patterns")
    print("=" * 40)
    
    # Example 1: Fallback to mock data
    print("\n1. Fallback to Mock Data")
    
    async def get_research_data(adapter=None):
        """Get research data with fallback."""
        if adapter and adapter.is_connected():
            try:
                # Try to use MCP tools
                tools = await adapter.list_tools()
                if "duckduckgo_search" in tools:
                    result = await adapter.execute_tool(
                        "duckduckgo_search", 
                        {"query": "MCP protocol research"}
                    )
                    return f"Live data: {result[:100]}..."
            except Exception as e:
                print(f"⚠️  MCP tool failed: {e}")
        
        # Fallback to mock data
        return "Mock data: MCP (Model Context Protocol) is a protocol for AI tool integration..."
    
    # Try with unavailable gateway
    adapter = MCPGatewayAdapter(
        transport=StreamingTransport("http://unavailable:8811"),
        timeout=2,
        max_retries=0
    )
    
    try:
        async with adapter:
            data = await get_research_data(adapter)
    except ConnectionError:
        data = await get_research_data(None)  # Fallback
    
    print(f"✓ Got data (with fallback): {data[:50]}...")
    
    # Example 2: Feature detection
    print("\n2. Feature Detection Pattern")
    
    class MCPService:
        def __init__(self, adapter):
            self.adapter = adapter
            self.available_features = set()
            
        async def initialize(self):
            """Detect available features."""
            try:
                async with self.adapter:
                    tools = await self.adapter.list_tools()
                    self.available_features = set(tools.keys())
                    print(f"✓ Detected features: {', '.join(self.available_features)}")
            except ConnectionError:
                print("ℹ️  MCP unavailable - running in offline mode")
                self.available_features = set()
        
        async def search(self, query):
            """Search with feature detection."""
            if "duckduckgo_search" in self.available_features:
                try:
                    return await self.adapter.execute_tool("duckduckgo_search", {"query": query})
                except Exception as e:
                    print(f"⚠️  Search tool failed: {e}")
            
            return f"Offline search result for: {query}"
    
    service = MCPService(adapter)
    await service.initialize()
    result = await service.search("test query")
    print(f"✓ Search result: {result[:50]}...")


async def crewai_error_integration():
    """Demonstrate error handling in CrewAI context."""
    print("\n🤖 CrewAI Error Integration")
    print("=" * 35)
    
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    
    try:
        async with adapter:
            factory = MCPToolFactory(adapter)
            
            # Create tools with error handling
            try:
                tools = await factory.create_crewai_tools()
                print(f"✓ Created {len(tools)} CrewAI tools successfully")
                
                # Test individual tool error handling
                if tools:
                    tool_name = list(tools.keys())[0]
                    tool = tools[tool_name]
                    
                    try:
                        # This might fail depending on the tool
                        result = tool._run(invalid_param="test")
                        print(f"⚠️  Tool executed with invalid params: {result[:50]}...")
                    except ToolExecutionError as e:
                        print(f"✓ Tool correctly handled execution error: {e}")
                    except Exception as e:
                        print(f"✓ Tool error handling: {type(e).__name__}: {e}")
                        
            except Exception as e:
                print(f"❌ Tool creation failed: {e}")
                print("💡 This would cause CrewAI to run without MCP tools")
                
    except ConnectionError:
        print("ℹ️  Gateway unavailable - demonstrating offline CrewAI handling")
        print("💡 CrewAI agents would run without MCP tools in this case")


async def main():
    """Run all error handling examples."""
    print("⚠️  MCP Error Handling Examples")
    print("=" * 50)
    
    # Connection errors
    await connection_error_handling()
    
    # Tool execution errors
    await tool_execution_error_handling()
    
    # Resource cleanup
    await resource_cleanup_patterns()
    
    # Graceful degradation
    await graceful_degradation_patterns()
    
    # CrewAI integration errors
    await crewai_error_integration()
    
    print("\n✨ Error handling examples completed!")
    print("\nKey patterns demonstrated:")
    print("1. Proper exception catching and handling")
    print("2. Automatic resource cleanup with context managers")
    print("3. Retry mechanisms with exponential backoff")
    print("4. Graceful degradation when services are unavailable")
    print("5. Feature detection for robust service integration")


if __name__ == "__main__":
    asyncio.run(main())