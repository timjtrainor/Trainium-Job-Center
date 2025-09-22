"""Tests for MCP Gateway Adapter (Phase 4).

Test suite for the main MCPGatewayAdapter class, configuration management,
and health monitoring functionality.
"""

import pytest
import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

# Import MCP modules
from app.services.mcp.mcp_adapter import MCPGatewayAdapter, ConfigurationError
from app.services.mcp.mcp_config import MCPConfig
from app.services.mcp.mcp_health import MCPHealthMonitor, HealthCheckResult
from app.services.mcp.mcp_transport import MCPTransport
from app.services.mcp.mcp_exceptions import MCPError, ConnectionError, HandshakeError


class MockTransport(MCPTransport):
    """Mock transport for testing."""
    
    def __init__(self):
        super().__init__()
        self.connect_should_fail = False
        self.connect_call_count = 0
        self.disconnect_call_count = 0
        
    async def connect(self):
        self.connect_call_count += 1
        if self.connect_should_fail:
            raise Exception("Mock connection failure")
        self._connected = True
        
    async def disconnect(self):
        self.disconnect_call_count += 1
        self._connected = False
        
    async def send_message(self, message: Dict[str, Any]):
        pass
        
    async def receive_message(self) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": 1, "result": {}}


@pytest.fixture
def mock_transport():
    """Create mock transport for testing."""
    return MockTransport()


@pytest.fixture
def adapter(mock_transport):
    """Create adapter instance with mock transport."""
    return MCPGatewayAdapter(
        transport=mock_transport,
        timeout=1,  # Short timeout for tests
        max_retries=1,  # Minimal retries for tests
        log_level="DEBUG"
    )


class TestMCPGatewayAdapter:
    """Test cases for MCPGatewayAdapter class."""
    
    def test_adapter_initialization(self, adapter, mock_transport):
        """Test adapter initialization."""
        assert adapter.transport == mock_transport
        assert adapter.timeout == 1
        assert adapter.max_retries == 1
        assert not adapter.is_connected()
        assert adapter.session is None
        
        # Check metrics are initialized
        metrics = adapter.get_metrics()
        assert metrics["total_requests"] == 0
        assert metrics["total_errors"] == 0
        assert not metrics["connected"]
        
    @pytest.mark.asyncio
    async def test_successful_connection(self, adapter, mock_transport):
        """Test successful connection establishment."""
        # Mock successful session creation
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.is_active = True
            mock_session.server_capabilities = {"tools": {"listChanged": True}}
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value = mock_session
            
            # Test connection
            await adapter.connect()
            
            assert adapter.is_connected()
            assert mock_transport.connect_call_count == 1
            mock_session.__aenter__.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_connection_with_retries(self, adapter, mock_transport):
        """Test connection with retry logic."""
        # Mock session that fails first time then succeeds
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.is_active = True
            mock_session.server_capabilities = {}
            
            # First call fails, second succeeds
            call_count = 0
            async def mock_aenter():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("First attempt fails")
                return mock_session
                
            mock_session.__aenter__ = mock_aenter
            mock_session_class.return_value = mock_session
            
            # Test connection
            await adapter.connect()
            
            assert adapter.is_connected()
            assert call_count == 2  # Retry worked
            
    @pytest.mark.asyncio
    async def test_connection_failure_exhausts_retries(self, adapter, mock_transport):
        """Test connection failure after all retries."""
        # Mock session that always fails
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(side_effect=Exception("Always fails"))
            mock_session_class.return_value = mock_session
            
            # Test connection should fail
            with pytest.raises(MCPError) as excinfo:
                await adapter.connect()
                
            assert "Failed to connect after 2 attempts" in str(excinfo.value)
            assert not adapter.is_connected()
            
    @pytest.mark.asyncio
    async def test_disconnect(self, adapter, mock_transport):
        """Test graceful disconnection."""
        # Mock connected session
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.is_active = True
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Connect first
            await adapter.connect()
            assert adapter.is_connected()
            
            # Test disconnect
            await adapter.disconnect()
            
            assert not adapter.is_connected()
            assert adapter.session is None
            mock_session.__aexit__.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_context_manager_success(self, adapter, mock_transport):
        """Test adapter as async context manager - success case."""
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.is_active = True
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Test context manager
            async with adapter as connected_adapter:
                assert connected_adapter == adapter
                assert adapter.is_connected()
                
            # After context exit
            assert not adapter.is_connected()
            mock_session.__aexit__.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_context_manager_connection_failure(self, adapter, mock_transport):
        """Test context manager with connection failure."""
        mock_transport.connect_should_fail = True
        
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
            mock_session_class.return_value = mock_session
            
            # Context manager should raise exception
            with pytest.raises(MCPError):
                async with adapter:
                    pass
                    
            assert not adapter.is_connected()
            
    @pytest.mark.asyncio
    async def test_list_tools_success(self, adapter, mock_transport):
        """Test successful tool listing."""
        # Setup connected adapter
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.is_active = True
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value = mock_session
            
            await adapter.connect()
            
            # Mock tool manager
            mock_tools = {"test_tool": {"name": "test_tool", "description": "A test tool"}}
            adapter.tool_manager.discover_tools = AsyncMock(return_value=mock_tools)
            
            # Test list tools
            result = await adapter.list_tools()
            
            assert result == mock_tools
            adapter.tool_manager.discover_tools.assert_called_once()
            
            # Check metrics updated
            metrics = adapter.get_metrics()
            assert metrics["total_requests"] == 1
            
    @pytest.mark.asyncio
    async def test_list_tools_not_connected(self, adapter):
        """Test tool listing when not connected."""
        assert not adapter.is_connected()
        
        # Should raise MCPError
        with pytest.raises(MCPError) as excinfo:
            await adapter.list_tools()
            
        assert "Not connected" in str(excinfo.value)
        
    @pytest.mark.asyncio
    async def test_get_tool_info_success(self, adapter, mock_transport):
        """Test successful tool info retrieval."""
        # Setup connected adapter
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.is_active = True
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value = mock_session
            
            await adapter.connect()
            
            # Mock tool manager
            mock_tool_info = {"name": "test_tool", "description": "A test tool"}
            adapter.tool_manager.get_tool_info = AsyncMock(return_value=mock_tool_info)
            
            # Test get tool info
            result = await adapter.get_tool_info("test_tool")
            
            assert result == mock_tool_info
            adapter.tool_manager.get_tool_info.assert_called_once_with("test_tool")
            
    @pytest.mark.asyncio
    async def test_execute_tool_success(self, adapter, mock_transport):
        """Test successful tool execution."""
        # Setup connected adapter
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.is_active = True
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value = mock_session
            
            await adapter.connect()
            
            # Mock tool manager
            mock_result = {
                "success": True,
                "result": {"output": "test output"},
                "metadata": {"execution_time": 0.1}
            }
            adapter.tool_manager.execute_tool = AsyncMock(return_value=mock_result)
            
            # Test execute tool
            arguments = {"arg1": "value1"}
            result = await adapter.execute_tool("test_tool", arguments)
            
            assert result == mock_result
            adapter.tool_manager.execute_tool.assert_called_once_with("test_tool", arguments)
            
    @pytest.mark.asyncio
    async def test_health_check(self, adapter, mock_transport):
        """Test health check functionality."""
        # Setup connected adapter
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.is_active = True
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value = mock_session
            
            await adapter.connect()
            
            # Mock tool manager for health check
            mock_tools = {"tool1": {}, "tool2": {}}
            adapter.tool_manager.discover_tools = AsyncMock(return_value=mock_tools)
            
            # Test health check
            health = await adapter.health_check()
            
            assert health["status"] == "healthy"
            assert health["tools_available"] == 2
            assert health["connection"]["connected"] is True
            
    def test_get_connection_info(self, adapter, mock_transport):
        """Test connection info retrieval."""
        info = adapter.get_connection_info()
        
        assert info["connected"] is False
        assert info["transport_type"] == "MockTransport"
        assert info["timeout"] == 1
        assert info["max_retries"] == 1
        
    def test_get_metrics(self, adapter):
        """Test metrics retrieval."""
        metrics = adapter.get_metrics()
        
        assert "uptime_seconds" in metrics
        assert metrics["total_requests"] == 0
        assert metrics["total_errors"] == 0
        assert metrics["error_rate"] == 0.0
        assert metrics["connected"] is False


class TestMCPConfig:
    """Test cases for MCPConfig class."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        assert MCPConfig.DEFAULT_GATEWAY_URL == "http://mcp-gateway:8811"
        assert MCPConfig.DEFAULT_TRANSPORT_TYPE == "streaming"
        assert MCPConfig.DEFAULT_TIMEOUT == 30
        assert MCPConfig.DEFAULT_MAX_RETRIES == 3
        assert MCPConfig.DEFAULT_LOG_LEVEL == "INFO"
        
    def test_from_dict_with_defaults(self):
        """Test creating adapter from dictionary with defaults."""
        config_dict = {"transport_type": "stdio"}
        
        adapter = MCPConfig.from_dict(config_dict)
        
        assert isinstance(adapter, MCPGatewayAdapter)
        assert adapter.timeout == MCPConfig.DEFAULT_TIMEOUT
        assert adapter.max_retries == MCPConfig.DEFAULT_MAX_RETRIES
        
    def test_from_dict_validation_errors(self):
        """Test configuration validation."""
        # Invalid transport type
        with pytest.raises(ConfigurationError) as excinfo:
            MCPConfig.from_dict({"transport_type": "invalid"})
            
        assert "Unsupported transport type" in str(excinfo.value)
        
        # Invalid timeout
        with pytest.raises(ConfigurationError) as excinfo:
            MCPConfig.from_dict({"timeout": -1})
            
        assert "Invalid timeout" in str(excinfo.value)
        
        # Invalid log level
        with pytest.raises(ConfigurationError) as excinfo:
            MCPConfig.from_dict({"log_level": "INVALID"})
            
        assert "Invalid log_level" in str(excinfo.value)
        
    @patch.dict(os.environ, {
        "MCP_GATEWAY_URL": "http://test:8811",
        "MCP_GATEWAY_TRANSPORT": "stdio",
        "MCP_GATEWAY_TIMEOUT": "10",
        "MCP_GATEWAY_MAX_RETRIES": "2",
        "MCP_LOG_LEVEL": "DEBUG"
    })
    def test_from_environment(self):
        """Test creating adapter from environment variables."""
        adapter = MCPConfig.from_environment()
        
        assert isinstance(adapter, MCPGatewayAdapter)
        assert adapter.timeout == 10
        assert adapter.max_retries == 2
        
    def test_get_config_info(self):
        """Test configuration information retrieval."""
        info = MCPConfig.get_config_info()
        
        assert "defaults" in info
        assert "current_env" in info
        assert "supported_transports" in info
        assert "environment_variables" in info
        
        assert "streaming" in info["supported_transports"]
        assert "stdio" in info["supported_transports"]
        
    def test_create_test_config(self):
        """Test test configuration creation."""
        config = MCPConfig.create_test_config()
        
        assert config["transport_type"] == "stdio"
        assert config["timeout"] == 5
        assert config["max_retries"] == 1
        assert config["log_level"] == "DEBUG"


class TestMCPHealthMonitor:
    """Test cases for MCPHealthMonitor class."""
    
    @pytest.fixture
    def health_monitor(self, adapter):
        """Create health monitor for testing."""
        return MCPHealthMonitor(adapter, check_interval=1)
        
    def test_health_monitor_initialization(self, health_monitor, adapter):
        """Test health monitor initialization."""
        assert health_monitor.adapter == adapter
        assert health_monitor.check_interval == 1
        assert not health_monitor.is_monitoring
        assert health_monitor.last_health_check is None
        
    @pytest.mark.asyncio
    async def test_health_check_not_connected(self, health_monitor):
        """Test health check when adapter not connected."""
        result = await health_monitor.health_check()
        
        assert result.status == "unhealthy"
        assert "not connected" in " ".join(result.errors).lower()
        assert result.details["connected"] is False
        
    @pytest.mark.asyncio
    async def test_health_check_connected_healthy(self, health_monitor, adapter, mock_transport):
        """Test health check when adapter is connected and healthy."""
        # Setup connected adapter
        with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.is_active = True
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value = mock_session
            
            await adapter.connect()
            
            # Mock tool discovery
            mock_tools = {"tool1": {}, "tool2": {}}
            adapter.tool_manager.discover_tools = AsyncMock(return_value=mock_tools)
            
            # Test health check
            result = await health_monitor.health_check()
            
            assert result.status == "healthy"
            assert len(result.errors) == 0
            assert result.details["connected"] is True
            assert result.details["tools_available"] == 2
            
    @pytest.mark.asyncio
    async def test_automatic_monitoring(self, health_monitor):
        """Test automatic health monitoring start/stop."""
        assert not health_monitor.is_monitoring
        
        # Start monitoring
        await health_monitor.start_monitoring()
        assert health_monitor.is_monitoring
        
        # Give it a moment to run
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await health_monitor.stop_monitoring()
        assert not health_monitor.is_monitoring
        
    def test_get_metrics(self, health_monitor):
        """Test metrics retrieval."""
        metrics = health_monitor.get_metrics()
        
        assert "monitor" in metrics
        assert "adapter" in metrics
        assert "health" in metrics
        assert "thresholds" in metrics
        
        assert metrics["monitor"]["monitoring_active"] is False
        assert metrics["monitor"]["check_interval"] == 1
        
    def test_get_health_summary_no_check(self, health_monitor):
        """Test health summary when no check performed."""
        summary = health_monitor.get_health_summary()
        
        assert summary["status"] == "unknown"
        assert "No health check performed" in summary["message"]
        assert summary["timestamp"] is None
        
    @pytest.mark.asyncio
    async def test_get_health_summary_after_check(self, health_monitor):
        """Test health summary after performing check."""
        # Perform health check
        await health_monitor.health_check()
        
        summary = health_monitor.get_health_summary()
        
        assert summary["status"] in ["healthy", "degraded", "unhealthy"]
        assert isinstance(summary["message"], str)
        assert summary["timestamp"] is not None
        
    def test_reset_metrics(self, health_monitor):
        """Test metrics reset functionality."""
        # Capture initial state
        initial_time = health_monitor._start_time
        
        # Add some fake history
        health_monitor._metric_history.append(MagicMock())
        health_monitor._last_health_check = MagicMock()
        
        # Reset
        health_monitor.reset_metrics()
        
        assert len(health_monitor._metric_history) == 0
        assert health_monitor._last_health_check is None
        assert health_monitor._start_time > initial_time


class TestIntegration:
    """Integration tests combining multiple components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, mock_transport):
        """Test complete workflow from config to execution."""
        # Create adapter via config
        config_dict = {
            "transport_type": "stdio",
            "timeout": 5,
            "max_retries": 1,
            "log_level": "DEBUG"
        }
        
        with patch('app.services.mcp.mcp_config.StdioTransport', return_value=mock_transport):
            adapter = MCPConfig.from_dict(config_dict)
            
            # Setup health monitor
            health_monitor = MCPHealthMonitor(adapter, check_interval=1)
            
            # Mock session and tools for successful workflow
            with patch('app.services.mcp.mcp_adapter.MCPSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session.is_active = True
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock()
                mock_session_class.return_value = mock_session
                
                # Mock tool operations
                mock_tools = {"test_tool": {"name": "test_tool"}}
                adapter.tool_manager.discover_tools = AsyncMock(return_value=mock_tools)
                adapter.tool_manager.execute_tool = AsyncMock(return_value={
                    "success": True,
                    "result": {"output": "success"},
                    "metadata": {"execution_time": 0.1}
                })
                
                # Test complete workflow
                async with adapter as connected_adapter:
                    # List tools
                    tools = await connected_adapter.list_tools()
                    assert len(tools) == 1
                    
                    # Execute tool
                    result = await connected_adapter.execute_tool("test_tool", {})
                    assert result["success"] is True
                    
                    # Health check
                    health = await health_monitor.health_check()
                    assert health.status == "healthy"
                    
                    # Verify metrics
                    metrics = connected_adapter.get_metrics()
                    assert metrics["total_requests"] == 2  # list_tools + execute_tool