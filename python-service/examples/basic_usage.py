#!/usr/bin/env python3
"""Basic MCP Gateway Adapter Usage Example.

This example demonstrates the fundamental usage patterns of the MCP Gateway 
Adapter, including:
- Manual adapter configuration
- Environment-based configuration  
- Tool discovery and execution
- Basic error handling
- Connection lifecycle management
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
    ToolExecutionError
)


async def basic_example():
    """Basic usage example demonstrating core functionality."""
    print("🔧 Basic MCP Gateway Usage Example")
    print("=" * 50)
    
    # Method 1: Manual configuration with streaming transport
    print("\n📡 Method 1: Manual Configuration")
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(
        transport=transport,
        timeout=30,
        max_retries=3,
        log_level="INFO"
    )
    
    try:
        print(f"✓ Created adapter with {type(transport).__name__}")
        print(f"  - Gateway URL: {transport.gateway_url}")
        print(f"  - Timeout: {adapter.timeout}s")
        print(f"  - Max retries: {adapter.max_retries}")
        
        # Connect to the gateway
        print("\n🔗 Connecting to MCP Gateway...")
        async with adapter:
            print("✓ Connected successfully!")
            
            # Discover available tools
            print("\n🔍 Discovering available tools...")
            tools = await adapter.list_tools()
            print(f"✓ Found {len(tools)} tools:")
            
            for tool_name, tool_info in tools.items():
                print(f"  - {tool_name}: {tool_info.get('description', 'No description')}")
            
            # Execute a tool if available
            if tools:
                tool_name = list(tools.keys())[0]
                print(f"\n⚡ Executing tool: {tool_name}")
                
                # Get tool schema to understand required parameters
                tool_schema = tools[tool_name].get("inputSchema", {})
                properties = tool_schema.get("properties", {})
                
                # Create example arguments based on schema
                example_args = {}
                for prop_name, prop_info in properties.items():
                    if prop_info.get("type") == "string":
                        example_args[prop_name] = f"example_{prop_name}"
                    elif prop_info.get("type") == "integer":
                        example_args[prop_name] = 42
                    elif prop_info.get("type") == "boolean":
                        example_args[prop_name] = True
                
                try:
                    result = await adapter.execute_tool(tool_name, example_args)
                    print(f"✓ Tool execution successful!")
                    print(f"  Result: {result[:200]}{'...' if len(str(result)) > 200 else ''}")
                except ToolExecutionError as e:
                    print(f"⚠️  Tool execution failed: {e}")
            else:
                print("ℹ️  No tools available for execution")
                
    except ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Make sure the MCP Gateway is running on http://localhost:8811")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def environment_config_example():
    """Example using environment-based configuration."""
    print("\n📡 Method 2: Environment Configuration")
    
    # Set example environment variables (normally set in shell or .env file)
    os.environ.setdefault("MCP_GATEWAY_URL", "http://localhost:8811")
    os.environ.setdefault("MCP_TRANSPORT_TYPE", "streaming")
    os.environ.setdefault("MCP_TIMEOUT", "30")
    os.environ.setdefault("MCP_MAX_RETRIES", "3")
    
    try:
        # Create adapter from environment
        adapter = MCPConfig.from_environment()
        print("✓ Created adapter from environment configuration")
        
        # Display configuration
        config_info = {
            "transport_type": type(adapter.transport).__name__,
            "timeout": adapter.timeout,
            "max_retries": adapter.max_retries
        }
        
        for key, value in config_info.items():
            print(f"  - {key}: {value}")
            
        # Test connection
        print("\n🔗 Testing connection...")
        async with adapter:
            print("✓ Environment-configured connection successful!")
            
            # Get connection statistics
            connection_info = adapter.get_connection_info()
            print("📊 Connection Info:")
            for key, value in connection_info.items():
                print(f"  - {key}: {value}")
                
    except Exception as e:
        print(f"❌ Environment configuration failed: {e}")


async def error_handling_example():
    """Demonstrate error handling patterns."""
    print("\n⚠️  Error Handling Example")
    print("=" * 30)
    
    # Example 1: Connection timeout
    print("\n1. Connection Timeout Example")
    transport = StreamingTransport("http://nonexistent-host:8811")
    adapter = MCPGatewayAdapter(transport=transport, timeout=5, max_retries=1)
    
    try:
        async with adapter:
            await adapter.list_tools()
    except ConnectionError as e:
        print(f"✓ Caught expected ConnectionError: {e}")
    except Exception as e:
        print(f"✓ Caught error: {type(e).__name__}: {e}")
    
    # Example 2: Invalid tool execution
    print("\n2. Invalid Tool Execution Example")
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    
    try:
        async with adapter:
            # Try to execute a non-existent tool
            await adapter.execute_tool("nonexistent_tool", {"arg": "value"})
    except ToolExecutionError as e:
        print(f"✓ Caught expected ToolExecutionError: {e}")
    except ConnectionError:
        print("ℹ️  Gateway not available for this example")
    except Exception as e:
        print(f"✓ Caught error: {type(e).__name__}: {e}")


async def health_monitoring_example():
    """Demonstrate health monitoring capabilities."""
    print("\n🏥 Health Monitoring Example")
    print("=" * 35)
    
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    
    try:
        async with adapter:
            # Get health information
            health_info = adapter.get_connection_info()
            print("📊 Adapter Health:")
            for key, value in health_info.items():
                print(f"  - {key}: {value}")
                
    except ConnectionError:
        print("ℹ️  Gateway not available - showing offline health info")
        health_info = adapter.get_connection_info()
        print("📊 Adapter Health (Offline):")
        for key, value in health_info.items():
            print(f"  - {key}: {value}")


async def main():
    """Run all examples."""
    print("🚀 MCP Gateway Adapter Examples")
    print("=" * 50)
    
    # Basic usage example
    await basic_example()
    
    # Environment configuration example  
    await environment_config_example()
    
    # Error handling patterns
    await error_handling_example()
    
    # Health monitoring
    await health_monitoring_example()
    
    print("\n✨ Examples completed!")
    print("\nNext steps:")
    print("1. Start the MCP Gateway: python mcp_gateway.py")
    print("2. Run this example again to see full functionality")
    print("3. Try the CrewAI integration example: python examples/crewai_integration.py")


if __name__ == "__main__":
    asyncio.run(main())