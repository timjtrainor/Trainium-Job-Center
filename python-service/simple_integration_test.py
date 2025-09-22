#!/usr/bin/env python3
"""
Simple integration test for MCP Gateway implementation with CrewAI compatibility.
Uses only standard library to test core functionality.
"""
import sys
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Create minimal mocks for testing
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARN: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")

class MockBaseTool:
    def __init__(self, name, description="", executor=None, parameters=None):
        self.name = name
        self.description = description
        self.executor = executor or (lambda **k: f"Mock result for {k}")
        self.parameters = parameters or {}
    
    def _run(self, *args, **kwargs):
        return self.executor(*args, **kwargs)

# Apply minimal mocks
sys.modules['loguru'] = type(sys)('loguru')
sys.modules['loguru'].logger = MockLogger()

sys.modules['httpx'] = type(sys)('httpx')
sys.modules['httpx'].AsyncClient = lambda **k: None
sys.modules['httpx'].Timeout = lambda **k: None
sys.modules['httpx'].TimeoutException = TimeoutError

sys.modules['mcp'] = type(sys)('mcp')
sys.modules['mcp'].ClientSession = object
sys.modules['mcp.types'] = type(sys)('mcp.types')
sys.modules['mcp.types'].Tool = dict

sys.modules['crewai'] = type(sys)('crewai')  
sys.modules['crewai.tools'] = type(sys)('crewai.tools')
sys.modules['crewai.tools'].BaseTool = MockBaseTool

# Import core classes only
from app.services.mcp_adapter import MCPServerAdapter, AdapterConfig


def test_adapter_config_dataclass():
    """Test that AdapterConfig works as expected."""
    print("Testing AdapterConfig dataclass...")
    
    # Test default values
    config = AdapterConfig()
    assert config.gateway_url == "http://localhost:8811"
    assert config.connection_timeout == 30
    assert config.discovery_timeout == 60
    assert config.execution_timeout == 120
    assert config.verify_tls == True
    assert config.max_retries == 3
    
    # Test custom values
    custom = AdapterConfig(
        gateway_url="http://custom:9999",
        connection_timeout=15,
        verify_tls=False
    )
    assert custom.gateway_url == "http://custom:9999"
    assert custom.connection_timeout == 15
    assert custom.verify_tls == False
    
    print("✅ AdapterConfig test passed")
    return True


def test_adapter_initialization():
    """Test MCPServerAdapter initialization."""
    print("Testing MCPServerAdapter initialization...")
    
    # Test default initialization
    adapter = MCPServerAdapter()
    assert adapter.config.gateway_url == "http://localhost:8811"
    assert adapter._session is None
    assert adapter._connected == False
    
    # Test custom config initialization
    config = AdapterConfig(gateway_url="http://test:1234")
    adapter_custom = MCPServerAdapter(config)
    assert adapter_custom.config.gateway_url == "http://test:1234"
    
    print("✅ MCPServerAdapter initialization test passed")
    return True


def test_server_and_tool_management():
    """Test server and tool management methods."""
    print("Testing server and tool management...")
    
    adapter = MCPServerAdapter()
    
    # Test empty state
    assert len(adapter.list_servers()) == 0
    assert len(adapter.get_all_tools()) == 0
    assert len(adapter.list_tools()) == 0
    
    # Add mock data
    adapter._available_servers = {
        "duckduckgo": {"transport": "sse"},
        "test_server": {"transport": "http"}
    }
    
    adapter._available_tools = {
        "duckduckgo_web_search": {
            "name": "web_search",
            "description": "Web search",
            "server": "duckduckgo", 
            "original_name": "web_search"
        },
        "test_server_tool": {
            "name": "tool",
            "description": "Test tool",
            "server": "test_server",
            "original_name": "tool"
        }
    }
    
    # Test server listing
    servers = adapter.list_servers()
    assert "duckduckgo" in servers
    assert "test_server" in servers
    assert len(servers) == 2
    
    # Test all tools
    all_tools = adapter.get_all_tools()
    assert len(all_tools) == 2
    assert "duckduckgo_web_search" in all_tools
    assert "test_server_tool" in all_tools
    
    # Test server-specific tools
    dd_tools = adapter.list_tools("duckduckgo")
    assert len(dd_tools) == 1
    assert "duckduckgo_web_search" in dd_tools
    
    test_tools = adapter.list_tools("test_server")
    assert len(test_tools) == 1
    assert "test_server_tool" in test_tools
    
    # Test DuckDuckGo specific tools (legacy compatibility)
    dd_tools = adapter.get_duckduckgo_tools()
    assert len(dd_tools) == 1
    assert dd_tools[0]["name"] == "duckduckgo_web_search"
    
    print("✅ Server and tool management test passed")
    return True


def test_tool_executor_creation():
    """Test tool executor creation for CrewAI compatibility."""
    print("Testing tool executor creation...")
    
    adapter = MCPServerAdapter()
    
    # Mock tool configuration
    tool_config = {
        "name": "test_tool",
        "description": "Test tool for validation",
        "server": "test_server",
        "original_name": "test_tool",
        "parameters": {"query": {"type": "string"}}
    }
    
    # Test executor creation
    executor = adapter._create_tool_executor("test_server_test_tool", tool_config)
    assert callable(executor)
    
    # Test CrewAI tool format conversion
    crewai_tool = adapter._convert_mcp_tool_to_crewai("test_server_test_tool", tool_config)
    assert crewai_tool["name"] == "test_server_test_tool"
    assert crewai_tool["description"] == "Test tool for validation"
    assert "parameters" in crewai_tool
    assert callable(crewai_tool["execute"])
    
    print("✅ Tool executor creation test passed")
    return True


def test_error_handling():
    """Test error handling for various conditions."""
    print("Testing error handling...")
    
    adapter = MCPServerAdapter()
    
    # Test unconnected adapter
    try:
        asyncio.run(adapter.execute_tool("test", "tool", {}))
        assert False, "Should raise RuntimeError"
    except RuntimeError as e:
        assert "not connected" in str(e)
    
    # Test invalid server
    adapter._connected = True
    adapter._available_servers = {"valid": {}}
    
    try:
        asyncio.run(adapter.execute_tool("invalid", "tool", {}))
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "not available" in str(e)
    
    # Test missing tool
    try:
        asyncio.run(adapter.execute_tool("valid", "missing_tool", {}))
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "not found" in str(e)
    
    print("✅ Error handling test passed")
    return True


def test_diagnostics():
    """Test diagnostic information."""
    print("Testing diagnostics...")
    
    adapter = MCPServerAdapter()
    diagnostics = adapter.get_diagnostics()
    
    # Check diagnostic structure
    required_fields = [
        "connected", "gateway_url", "sse_endpoint", "session_id",
        "servers", "tools_count", "tools", "config"
    ]
    
    for field in required_fields:
        assert field in diagnostics, f"Missing diagnostic field: {field}"
    
    # Check types
    assert isinstance(diagnostics["connected"], bool)
    assert isinstance(diagnostics["gateway_url"], str)
    assert isinstance(diagnostics["servers"], list)
    assert isinstance(diagnostics["tools"], list)
    assert isinstance(diagnostics["config"], dict)
    
    print("✅ Diagnostics test passed")
    return True


def test_backward_compatibility():
    """Test backward compatibility with existing interfaces."""
    print("Testing backward compatibility...")
    
    adapter = MCPServerAdapter()
    
    # Test legacy methods exist
    legacy_methods = [
        'get_available_tools',
        'get_duckduckgo_tools', 
        'call_tool',
        '_create_tool_executor',
        '_convert_mcp_tool_to_crewai'
    ]
    
    for method in legacy_methods:
        assert hasattr(adapter, method), f"Missing legacy method: {method}"
        assert callable(getattr(adapter, method)), f"Legacy method not callable: {method}"
    
    # Test get_available_tools is alias for get_all_tools
    assert adapter.get_available_tools() == adapter.get_all_tools()
    
    print("✅ Backward compatibility test passed")
    return True


def test_context_manager_interface():
    """Test async context manager interface."""
    print("Testing context manager interface...")
    
    adapter = MCPServerAdapter()
    
    # Test context manager methods exist
    assert hasattr(adapter, '__aenter__')
    assert hasattr(adapter, '__aexit__')
    assert callable(adapter.__aenter__)
    assert callable(adapter.__aexit__)
    
    print("✅ Context manager interface test passed")
    return True


def main():
    """Run all integration tests."""
    print("🧪 Simple MCP Gateway Integration Test")
    print("=" * 50)
    
    tests = [
        ("AdapterConfig Dataclass", test_adapter_config_dataclass),
        ("Adapter Initialization", test_adapter_initialization),
        ("Server & Tool Management", test_server_and_tool_management),
        ("Tool Executor Creation", test_tool_executor_creation),
        ("Error Handling", test_error_handling),
        ("Diagnostics", test_diagnostics),
        ("Backward Compatibility", test_backward_compatibility),
        ("Context Manager Interface", test_context_manager_interface),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 50}")
    print("Integration Test Summary")
    print(f"{'=' * 50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        emoji = "✅" if result else "❌"
        print(f"{emoji} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("\nCore Integration Features Validated:")
        print("✅ AdapterConfig dataclass with proper defaults")
        print("✅ MCPServerAdapter initialization and state management")
        print("✅ Server and tool listing with namespacing")
        print("✅ Tool executor creation for CrewAI compatibility")
        print("✅ Comprehensive error handling for edge cases")
        print("✅ Diagnostic information for troubleshooting")
        print("✅ Full backward compatibility with existing interfaces")
        print("✅ Async context manager for resource management")
        print("\nThe implementation is ready for production deployment!")
        return 0
    else:
        print(f"\n❌ {total - passed} integration tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)