#!/usr/bin/env python3
"""
Phase 4 MCP Gateway Adapter Demonstration

This script demonstrates the main functionality of the Phase 4 implementation,
including adapter creation, configuration management, and health monitoring.
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, '/home/runner/work/Trainium-Job-Center/Trainium-Job-Center/python-service')

from app.services.mcp import (
    MCPGatewayAdapter,
    MCPConfig,
    MCPHealthMonitor,
    StdioTransport,
    StreamingTransport,
    ConfigurationError
)


async def demo_basic_adapter_usage():
    """Demonstrate basic adapter usage."""
    print("🔧 Phase 4 Demo: Basic Adapter Usage")
    print("=" * 50)
    
    # Create adapter with stdio transport (for demo purposes)
    transport = StdioTransport()
    adapter = MCPGatewayAdapter(
        transport=transport,
        timeout=10,
        max_retries=2,
        log_level="INFO"
    )
    
    print(f"✓ Created adapter with {type(transport).__name__}")
    print(f"  - Timeout: {adapter.timeout}s")
    print(f"  - Max retries: {adapter.max_retries}")
    print(f"  - Connected: {adapter.is_connected()}")
    
    # Get connection info
    connection_info = adapter.get_connection_info()
    print(f"\n📊 Connection Info:")
    for key, value in connection_info.items():
        print(f"  - {key}: {value}")
    
    # Get metrics
    metrics = adapter.get_metrics()
    print(f"\n📈 Metrics:")
    print(f"  - Uptime: {metrics['uptime_seconds']:.2f}s")
    print(f"  - Total requests: {metrics['total_requests']}")
    print(f"  - Total errors: {metrics['total_errors']}")
    print(f"  - Error rate: {metrics['error_rate']:.2%}")
    
    print("\n✅ Basic adapter demo completed\n")


async def demo_configuration_management():
    """Demonstrate configuration management."""
    print("⚙️  Phase 4 Demo: Configuration Management")
    print("=" * 50)
    
    # Show configuration info
    config_info = MCPConfig.get_config_info()
    print("📋 Available Configuration:")
    print(f"  - Supported transports: {', '.join(config_info['supported_transports'])}")
    print(f"  - Default gateway URL: {config_info['defaults']['gateway_url']}")
    print(f"  - Default timeout: {config_info['defaults']['timeout']}s")
    print(f"  - Default max retries: {config_info['defaults']['max_retries']}")
    
    # Create adapter from dictionary configuration
    config_dict = {
        "transport_type": "stdio",
        "timeout": 15,
        "max_retries": 1,
        "log_level": "DEBUG"
    }
    
    print(f"\n🔧 Creating adapter from config: {config_dict}")
    adapter = MCPConfig.from_dict(config_dict)
    
    print(f"✓ Adapter created successfully")
    print(f"  - Transport: {type(adapter.transport).__name__}")
    print(f"  - Timeout: {adapter.timeout}s")
    print(f"  - Max retries: {adapter.max_retries}")
    
    # Test configuration validation
    print(f"\n🚨 Testing invalid configuration...")
    invalid_configs = [
        {"transport_type": "invalid"},
        {"timeout": -1},
        {"log_level": "INVALID"}
    ]
    
    for invalid_config in invalid_configs:
        try:
            MCPConfig.from_dict(invalid_config)
            print(f"  ❌ Should have failed: {invalid_config}")
        except ConfigurationError as e:
            print(f"  ✓ Correctly rejected: {invalid_config}")
            print(f"    Error: {e}")
    
    # Create test configuration
    test_config = MCPConfig.create_test_config(transport_type="stdio", timeout=3)
    print(f"\n🧪 Test configuration created: {test_config}")
    
    print("\n✅ Configuration management demo completed\n")


async def demo_health_monitoring():
    """Demonstrate health monitoring functionality."""
    print("🏥 Phase 4 Demo: Health Monitoring")
    print("=" * 50)
    
    # Create adapter and health monitor
    transport = StdioTransport()
    adapter = MCPGatewayAdapter(
        transport=transport,
        timeout=5,
        max_retries=1,
        log_level="INFO"
    )
    
    health_monitor = MCPHealthMonitor(adapter, check_interval=2)
    
    print(f"✓ Created health monitor")
    print(f"  - Check interval: {health_monitor.check_interval}s")
    print(f"  - Monitoring active: {health_monitor.is_monitoring}")
    
    # Perform health check
    print(f"\n🔍 Performing health check...")
    health_result = await health_monitor.health_check()
    
    print(f"  - Status: {health_result.status}")
    print(f"  - Duration: {health_result.duration_ms:.1f}ms")
    print(f"  - Connected: {health_result.details.get('connected', False)}")
    print(f"  - Errors: {len(health_result.errors)}")
    
    if health_result.errors:
        for error in health_result.errors:
            print(f"    • {error}")
    
    # Get health summary
    summary = health_monitor.get_health_summary()
    print(f"\n📋 Health Summary:")
    print(f"  - Status: {summary['status']}")
    print(f"  - Message: {summary['message']}")
    print(f"  - Tools available: {summary['tools_available']}")
    
    # Get detailed metrics
    monitor_metrics = health_monitor.get_metrics()
    print(f"\n📊 Health Monitor Metrics:")
    print(f"  - Monitor uptime: {monitor_metrics['monitor']['uptime_seconds']:.2f}s")
    print(f"  - Last check timestamp: {monitor_metrics['monitor']['last_check_timestamp']}")
    print(f"  - Error rate threshold: {monitor_metrics['thresholds']['error_rate_threshold']:.1%}")
    print(f"  - Response time threshold: {monitor_metrics['thresholds']['response_time_threshold']}s")
    
    print("\n✅ Health monitoring demo completed\n")


async def demo_context_manager():
    """Demonstrate context manager usage."""
    print("🔄 Phase 4 Demo: Context Manager Usage")
    print("=" * 50)
    
    # Create configuration
    config = {
        "transport_type": "stdio",
        "timeout": 10,
        "max_retries": 1,
        "log_level": "INFO"
    }
    
    print(f"🔧 Using configuration: {config}")
    
    # This would normally connect to a real MCP gateway
    # For demo purposes, we'll just show the pattern
    print(f"\n💡 Context manager pattern (would connect to real gateway):")
    print(f"""
    try:
        adapter = MCPConfig.from_dict(config)
        async with adapter as gateway:
            # Gateway is now connected and ready to use
            tools = await gateway.list_tools()
            tool_info = await gateway.get_tool_info("some_tool")
            result = await gateway.execute_tool("some_tool", {{"arg": "value"}})
            
            # Health check
            health = await gateway.health_check()
            
        # Gateway automatically disconnected when exiting context
    except Exception as e:
        print(f"Error: {{e}}")
    """)
    
    # Create adapter to show pattern
    adapter = MCPConfig.from_dict(config)
    print(f"✓ Adapter created with context manager support")
    print(f"  - Has __aenter__: {hasattr(adapter, '__aenter__')}")
    print(f"  - Has __aexit__: {hasattr(adapter, '__aexit__')}")
    
    print("\n✅ Context manager demo completed\n")


async def demo_error_handling():
    """Demonstrate error handling."""
    print("🚨 Phase 4 Demo: Error Handling")
    print("=" * 50)
    
    # Test configuration errors
    print("🔧 Testing configuration errors...")
    try:
        MCPConfig.from_dict({"transport_type": "nonexistent"})
    except ConfigurationError as e:
        print(f"  ✓ Configuration error caught: {e}")
    
    # Test adapter errors
    print(f"\n🔌 Testing adapter errors...")
    adapter = MCPGatewayAdapter(
        transport=StdioTransport(),
        timeout=1,
        max_retries=0,
        log_level="INFO"
    )
    
    # Test operations without connection
    operations = [
        ("list_tools", lambda: adapter.list_tools()),
        ("get_tool_info", lambda: adapter.get_tool_info("test")),
        ("execute_tool", lambda: adapter.execute_tool("test", {})),
        ("validate_tool_arguments", lambda: adapter.validate_tool_arguments("test", {}))
    ]
    
    for op_name, operation in operations:
        try:
            await operation()
            print(f"  ❌ {op_name} should have failed")
        except Exception as e:
            print(f"  ✓ {op_name} correctly failed: {type(e).__name__}")
    
    print("\n✅ Error handling demo completed\n")


async def main():
    """Run all demos."""
    print("🚀 Phase 4 MCP Gateway Adapter Demo")
    print("=" * 60)
    print("This demo showcases the Phase 4 implementation features:")
    print("- Main MCPGatewayAdapter class")
    print("- Configuration management (MCPConfig)")
    print("- Health monitoring (MCPHealthMonitor)")
    print("- Error handling and validation")
    print("- Context manager support")
    print("=" * 60)
    print()
    
    try:
        await demo_basic_adapter_usage()
        await demo_configuration_management()
        await demo_health_monitoring()
        await demo_context_manager()
        await demo_error_handling()
        
        print("🎉 All Phase 4 demos completed successfully!")
        print("\n📚 Key Features Demonstrated:")
        print("  ✓ MCPGatewayAdapter - Main coordination class")
        print("  ✓ MCPConfig - Environment and dict-based configuration")
        print("  ✓ MCPHealthMonitor - Health checks and metrics")
        print("  ✓ Context manager support for resource management")
        print("  ✓ Comprehensive error handling and validation")
        print("  ✓ Structured logging throughout")
        print("  ✓ Retry logic with exponential backoff")
        print("  ✓ Tool discovery and execution coordination")
        
        print("\n🔗 Ready for CrewAI Integration (Next Phase)")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())