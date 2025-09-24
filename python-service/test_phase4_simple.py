#!/usr/bin/env python3
"""
Simple test runner for Phase 4 MCP Gateway Adapter functionality.

This script performs basic validation of the Phase 4 implementation without
requiring pytest or external test frameworks.
"""

import asyncio
import sys
import traceback
from unittest.mock import AsyncMock, MagicMock

# Add parent directory to path
sys.path.insert(0, '/home/runner/work/Trainium-Job-Center/Trainium-Job-Center/python-service')

# Import MCP modules
from app.services.mcp.mcp_adapter import MCPGatewayAdapter, ConfigurationError
from app.services.mcp.mcp_config import MCPConfig
from app.services.mcp.mcp_health import MCPHealthMonitor
from app.services.mcp.mcp_transport import MCPTransport


class MockTransport(MCPTransport):
    """Mock transport for testing."""
    
    def __init__(self):
        super().__init__()
        self.connect_calls = 0
        self.disconnect_calls = 0
        
    async def connect(self):
        self.connect_calls += 1
        self._connected = True
        
    async def disconnect(self):
        self.disconnect_calls += 1
        self._connected = False
        
    async def send_message(self, message):
        pass
        
    async def receive_message(self):
        return {"jsonrpc": "2.0", "id": 1, "result": {}}


def test_adapter_initialization():
    """Test adapter initialization."""
    print("Testing adapter initialization...")
    
    transport = MockTransport()
    adapter = MCPGatewayAdapter(
        transport=transport,
        timeout=5,
        max_retries=1,
        log_level="DEBUG"
    )
    
    assert adapter.transport == transport
    assert adapter.timeout == 5
    assert adapter.max_retries == 1
    assert not adapter.is_connected()
    assert adapter.session is None
    
    # Check metrics
    metrics = adapter.get_metrics()
    assert metrics["total_requests"] == 0
    assert metrics["total_errors"] == 0
    assert not metrics["connected"]
    
    print("✓ Adapter initialization test passed")


async def test_connection_workflow():
    """Test connection and disconnection workflow."""
    print("Testing connection workflow...")
    
    transport = MockTransport()
    adapter = MCPGatewayAdapter(
        transport=transport,
        timeout=1,
        max_retries=1,
        log_level="DEBUG"
    )
    
    # Mock session for testing
    from unittest.mock import patch
    
    with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session.is_active = True
        mock_session.server_capabilities = {"tools": {"listChanged": True}}
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session_class.return_value = mock_session
        
        # Test connection
        await adapter.connect()
        assert adapter.is_connected()
        # The session.__aenter__ should have been called, which handles the transport connection
        mock_session.__aenter__.assert_called_once()
        
        # Test disconnection
        await adapter.disconnect()
        assert not adapter.is_connected()
        
    print("✓ Connection workflow test passed")


def test_config_validation():
    """Test configuration validation."""
    print("Testing configuration validation...")
    
    # Test valid configuration
    valid_config = {
        "transport_type": "stdio",
        "timeout": 30,
        "max_retries": 3,
        "log_level": "INFO"
    }
    
    try:
        adapter = MCPConfig.from_dict(valid_config)
        assert isinstance(adapter, MCPGatewayAdapter)
        print("✓ Valid configuration test passed")
    except Exception as e:
        print(f"✗ Valid configuration test failed: {e}")
        raise
    
    # Test invalid configuration
    invalid_configs = [
        {"transport_type": "invalid"},
        {"timeout": -1},
        {"max_retries": -1},
        {"log_level": "INVALID"}
    ]
    
    for invalid_config in invalid_configs:
        try:
            MCPConfig.from_dict(invalid_config)
            print(f"✗ Invalid config should have failed: {invalid_config}")
            raise AssertionError("Expected ConfigurationError")
        except ConfigurationError:
            print(f"✓ Invalid config correctly rejected: {invalid_config}")
        except Exception as e:
            print(f"✗ Unexpected error for invalid config {invalid_config}: {e}")
            raise


def test_health_monitor():
    """Test health monitoring functionality."""
    print("Testing health monitor...")
    
    transport = MockTransport()
    adapter = MCPGatewayAdapter(
        transport=transport,
        timeout=1,
        max_retries=1,
        log_level="DEBUG"
    )
    
    monitor = MCPHealthMonitor(adapter, check_interval=1)
    
    # Test initialization
    assert monitor.adapter == adapter
    assert monitor.check_interval == 1
    assert not monitor.is_monitoring
    assert monitor.last_health_check is None
    
    # Test metrics
    metrics = monitor.get_metrics()
    assert "monitor" in metrics
    assert "adapter" in metrics
    assert "health" in metrics
    
    print("✓ Health monitor test passed")


async def test_health_check():
    """Test health check functionality."""
    print("Testing health check...")
    
    transport = MockTransport()
    adapter = MCPGatewayAdapter(
        transport=transport,
        timeout=1,
        max_retries=1,
        log_level="DEBUG"
    )
    
    monitor = MCPHealthMonitor(adapter, check_interval=1)
    
    # Test health check when not connected
    result = await monitor.health_check()
    assert result.status == "unhealthy"
    assert "not connected" in " ".join(result.errors).lower()
    
    print("✓ Health check test passed")


async def test_context_manager():
    """Test adapter as context manager."""
    print("Testing context manager...")
    
    transport = MockTransport()
    adapter = MCPGatewayAdapter(
        transport=transport,
        timeout=1,
        max_retries=1,
        log_level="DEBUG"
    )
    
    from unittest.mock import patch
    
    with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session.is_active = True
        mock_session.server_capabilities = {"tools": {"listChanged": True}}  # Return dict, not coroutine
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session_class.return_value = mock_session
        
        # Test context manager
        async with adapter as connected_adapter:
            assert connected_adapter == adapter
            assert adapter.is_connected()
            
        # After context exit
        assert not adapter.is_connected()
        
    print("✓ Context manager test passed")


def test_config_info():
    """Test configuration information retrieval."""
    print("Testing configuration info...")
    
    info = MCPConfig.get_config_info()
    
    assert "defaults" in info
    assert "current_env" in info
    assert "supported_transports" in info
    assert "environment_variables" in info
    
    assert "streaming" in info["supported_transports"]
    assert "stdio" in info["supported_transports"]
    
    print("✓ Configuration info test passed")


def test_connection_info():
    """Test connection information retrieval."""
    print("Testing connection info...")
    
    transport = MockTransport()
    adapter = MCPGatewayAdapter(
        transport=transport,
        timeout=10,
        max_retries=2,
        log_level="INFO"
    )
    
    info = adapter.get_connection_info()
    
    assert info["connected"] is False
    assert info["transport_type"] == "MockTransport"
    assert info["timeout"] == 10
    assert info["max_retries"] == 2
    
    print("✓ Connection info test passed")


async def run_tests():
    """Run all tests."""
    print("Running Phase 4 MCP Gateway Adapter tests...\n")
    
    try:
        # Synchronous tests
        test_adapter_initialization()
        test_config_validation()
        test_health_monitor()
        test_config_info()
        test_connection_info()
        
        # Asynchronous tests
        await test_connection_workflow()
        await test_health_check()
        await test_context_manager()
        
        print("\n🎉 All Phase 4 tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Main test runner."""
    success = asyncio.run(run_tests())
    
    if success:
        print("\n✅ Phase 4 implementation is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Phase 4 implementation has issues!")
        sys.exit(1)


if __name__ == "__main__":
    main()