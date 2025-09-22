#!/usr/bin/env python3
"""
Simple validation script for the proper Docker MCP Gateway implementation.
Uses only standard library modules to validate the implementation.
"""
import sys
import asyncio
from pathlib import Path
from urllib.parse import urlparse

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

# Mock loguru for testing
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")

# Mock httpx for testing
class MockTimeout:
    def __init__(self, connect=30, read=60, write=120, pool=30):
        self.connect = connect
        self.read = read
        self.write = write
        self.pool = pool

class MockAsyncClient:
    def __init__(self, timeout=None, follow_redirects=False, verify=True):
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.verify = verify
        
    async def get(self, url, headers=None, timeout=None):
        return MockResponse(200, {"status": "ok"})
        
    async def post(self, url, json=None, timeout=None):
        return MockResponse(200, {"result": "ok"})
        
    async def aclose(self):
        pass

class MockResponse:
    def __init__(self, status_code, json_data=None, headers=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = headers or {}
        
    def json(self):
        return self._json_data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

# Mock MCP modules
class MockTool(dict):
    pass

# Apply mocks
sys.modules['loguru'] = type(sys)('loguru')
sys.modules['loguru'].logger = MockLogger()

sys.modules['httpx'] = type(sys)('httpx')
sys.modules['httpx'].AsyncClient = MockAsyncClient
sys.modules['httpx'].Timeout = MockTimeout
sys.modules['httpx'].TimeoutException = TimeoutError

sys.modules['mcp'] = type(sys)('mcp')
sys.modules['mcp'].ClientSession = object
sys.modules['mcp.types'] = type(sys)('mcp.types')
sys.modules['mcp.types'].Tool = MockTool

# Now import the actual implementation
from app.services.mcp_adapter import MCPServerAdapter, AdapterConfig, get_mcp_adapter


def test_adapter_config():
    """Test AdapterConfig dataclass."""
    print("Testing AdapterConfig...")
    
    # Test default config
    config = AdapterConfig()
    assert config.gateway_url == "http://localhost:8811"
    assert config.connection_timeout == 30
    assert config.discovery_timeout == 60
    assert config.execution_timeout == 120
    assert config.verify_tls == True
    assert config.max_retries == 3
    
    # Test custom config
    custom_config = AdapterConfig(
        gateway_url="http://custom:9999",
        connection_timeout=10,
        discovery_timeout=20,
        execution_timeout=30,
        verify_tls=False,
        max_retries=5
    )
    
    assert custom_config.gateway_url == "http://custom:9999"
    assert custom_config.connection_timeout == 10
    assert custom_config.discovery_timeout == 20
    assert custom_config.execution_timeout == 30
    assert custom_config.verify_tls == False
    assert custom_config.max_retries == 5
    
    print("✅ AdapterConfig test passed")
    return True


def test_adapter_initialization():
    """Test MCPServerAdapter initialization."""
    print("Testing MCPServerAdapter initialization...")
    
    # Test with default config
    adapter = MCPServerAdapter()
    assert adapter.config.gateway_url == "http://localhost:8811"
    assert adapter._session is None
    assert adapter._connected == False
    assert len(adapter._available_servers) == 0
    assert len(adapter._available_tools) == 0
    
    # Test with custom config
    config = AdapterConfig(gateway_url="http://test:1234")
    adapter_custom = MCPServerAdapter(config)
    assert adapter_custom.config.gateway_url == "http://test:1234"
    
    print("✅ MCPServerAdapter initialization test passed")
    return True


def test_diagnostics():
    """Test diagnostics functionality."""
    print("Testing diagnostics...")
    
    adapter = MCPServerAdapter()
    diagnostics = adapter.get_diagnostics()
    
    assert isinstance(diagnostics, dict)
    assert "connected" in diagnostics
    assert "gateway_url" in diagnostics
    assert "servers" in diagnostics
    assert "tools" in diagnostics
    assert "config" in diagnostics
    
    assert diagnostics["connected"] == False
    assert diagnostics["gateway_url"] == "http://localhost:8811"
    assert isinstance(diagnostics["servers"], list)
    assert isinstance(diagnostics["tools"], list)
    assert isinstance(diagnostics["config"], dict)
    
    print("✅ Diagnostics test passed")
    return True


def test_server_and_tool_management():
    """Test server and tool management methods."""
    print("Testing server and tool management...")
    
    adapter = MCPServerAdapter()
    
    # Test initial empty state
    assert len(adapter.list_servers()) == 0
    assert len(adapter.get_all_tools()) == 0
    assert len(adapter.list_tools()) == 0
    assert len(adapter.get_duckduckgo_tools()) == 0
    
    # Simulate connected state
    adapter._available_servers = {
        "duckduckgo": {"transport": "sse"},
        "linkedin-mcp-server": {"transport": "sse"}
    }
    
    adapter._available_tools = {
        "duckduckgo_web_search": {
            "name": "web_search",
            "description": "Web search tool",
            "server": "duckduckgo",
            "original_name": "web_search",
            "parameters": {}
        },
        "linkedin-mcp-server_search_jobs": {
            "name": "search_jobs",
            "description": "Job search tool",  
            "server": "linkedin-mcp-server",
            "original_name": "search_jobs",
            "parameters": {}
        }
    }
    
    # Test server listing
    servers = adapter.list_servers()
    assert len(servers) == 2
    assert "duckduckgo" in servers
    assert "linkedin-mcp-server" in servers
    
    # Test tool listing
    all_tools = adapter.get_all_tools()
    assert len(all_tools) == 2
    assert "duckduckgo_web_search" in all_tools
    assert "linkedin-mcp-server_search_jobs" in all_tools
    
    # Test server-specific tool listing
    duckduckgo_tools = adapter.list_tools("duckduckgo")
    assert len(duckduckgo_tools) == 1
    assert "duckduckgo_web_search" in duckduckgo_tools
    
    linkedin_tools = adapter.list_tools("linkedin-mcp-server")
    assert len(linkedin_tools) == 1
    assert "linkedin-mcp-server_search_jobs" in linkedin_tools
    
    # Test DuckDuckGo specific tools
    dd_tools = adapter.get_duckduckgo_tools()
    assert len(dd_tools) == 1
    assert dd_tools[0]["name"] == "duckduckgo_web_search"
    
    print("✅ Server and tool management test passed")
    return True


def test_context_manager_interface():
    """Test context manager interface."""
    print("Testing context manager interface...")
    
    config = AdapterConfig()
    adapter = MCPServerAdapter(config)
    
    # Test context manager methods exist
    assert hasattr(adapter, '__aenter__')
    assert hasattr(adapter, '__aexit__')
    
    # Test get_mcp_adapter function
    assert callable(get_mcp_adapter)
    
    print("✅ Context manager interface test passed")
    return True


def test_error_handling():
    """Test error handling."""
    print("Testing error handling...")
    
    adapter = MCPServerAdapter()
    
    # Test operations on unconnected adapter
    try:
        asyncio.run(adapter.execute_tool("test", "tool", {}))
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "not connected" in str(e)
    
    # Test invalid server
    adapter._connected = True
    adapter._available_servers = {"valid_server": {}}
    
    try:
        asyncio.run(adapter.execute_tool("invalid_server", "tool", {}))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not available" in str(e)
    
    print("✅ Error handling test passed")
    return True


def test_legacy_compatibility():
    """Test backward compatibility."""
    print("Testing legacy compatibility...")
    
    adapter = MCPServerAdapter()
    
    # Test legacy methods exist
    assert hasattr(adapter, 'get_available_tools')
    assert hasattr(adapter, 'get_duckduckgo_tools')
    assert hasattr(adapter, 'call_tool')
    
    # Test get_available_tools is alias for get_all_tools
    assert adapter.get_available_tools() == adapter.get_all_tools()
    
    print("✅ Legacy compatibility test passed")
    return True


def main():
    """Run all validation tests."""
    print("🚀 Simple MCP Gateway Implementation Validation")
    print("=" * 60)
    
    tests = [
        ("AdapterConfig", test_adapter_config),
        ("Adapter Initialization", test_adapter_initialization),
        ("Diagnostics", test_diagnostics),
        ("Server and Tool Management", test_server_and_tool_management),
        ("Context Manager Interface", test_context_manager_interface),
        ("Error Handling", test_error_handling),
        ("Legacy Compatibility", test_legacy_compatibility),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 60}")
    print("Validation Summary")
    print(f"{'=' * 60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        emoji = "✅" if result else "❌"
        print(f"{emoji} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validation tests passed!")
        print("\nImplementation Features Validated:")
        print("✅ Proper AdapterConfig dataclass with all required fields")
        print("✅ MCPServerAdapter initialization and state management")
        print("✅ Comprehensive diagnostics for troubleshooting")
        print("✅ Server and tool management methods")
        print("✅ Context manager interface for resource management")
        print("✅ Robust error handling for edge cases")
        print("✅ Backward compatibility with existing code")
        print("\nThe implementation is ready for integration!")
        return 0
    else:
        print(f"\n❌ {total - passed} validation tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)