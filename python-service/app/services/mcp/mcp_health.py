"""MCP Health Monitoring.

This module provides health monitoring and metrics collection for MCP adapter
operations, including connection health, performance metrics, and diagnostics.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .mcp_adapter import MCPGatewayAdapter
from .mcp_exceptions import MCPError

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: float
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class MetricSnapshot:
    """Snapshot of adapter metrics at a point in time."""
    timestamp: float
    uptime_seconds: float
    total_requests: int
    total_errors: int
    error_rate: float
    connected: bool
    tools_available: int
    connection_info: Dict[str, Any] = field(default_factory=dict)


class MCPHealthMonitor:
    """Health monitoring and metrics for MCP adapter."""
    
    def __init__(self, adapter: MCPGatewayAdapter, check_interval: int = 60):
        """Initialize health monitor.
        
        Args:
            adapter: MCP adapter instance to monitor
            check_interval: Interval between automatic health checks in seconds
        """
        self.adapter = adapter
        self.check_interval = check_interval
        
        # Health monitoring state
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        self._last_health_check: Optional[HealthCheckResult] = None
        
        # Metrics tracking
        self._start_time = time.time()
        self._metric_history: List[MetricSnapshot] = []
        self._max_history_size = 1000  # Keep last 1000 snapshots
        
        # Health thresholds
        self.error_rate_threshold = 0.1  # 10% error rate threshold
        self.response_time_threshold = 5.0  # 5 second response time threshold
        
        logger.info(
            "MCPHealthMonitor initialized",
            extra={
                "check_interval": check_interval,
                "error_rate_threshold": self.error_rate_threshold,
                "response_time_threshold": self.response_time_threshold
            }
        )
        
    async def health_check(self) -> HealthCheckResult:
        """Perform comprehensive health check on adapter.
        
        Returns:
            HealthCheckResult with detailed health information
        """
        start_time = time.time()
        timestamp = start_time
        errors = []
        details = {}
        
        try:
            logger.debug("Starting MCP adapter health check")
            
            # Basic connection check
            is_connected = self.adapter.is_connected()
            details["connected"] = is_connected
            
            if not is_connected:
                errors.append("MCP adapter not connected")
                
            # Get adapter metrics
            try:
                metrics = self.adapter.get_metrics()
                details["metrics"] = metrics
                
                # Check error rate
                error_rate = metrics.get("error_rate", 0)
                if error_rate > self.error_rate_threshold:
                    errors.append(f"High error rate: {error_rate:.2%} > {self.error_rate_threshold:.2%}")
                    
            except Exception as e:
                errors.append(f"Failed to get adapter metrics: {e}")
                
            # Test tool discovery if connected
            tools_available = 0
            if is_connected:
                try:
                    tools_start = time.time()
                    tools = await self.adapter.list_tools()
                    tools_duration = time.time() - tools_start
                    
                    tools_available = len(tools)
                    details["tools_available"] = tools_available
                    details["tool_discovery_time_ms"] = tools_duration * 1000
                    
                    # Check response time
                    if tools_duration > self.response_time_threshold:
                        errors.append(
                            f"Slow tool discovery: {tools_duration:.2f}s > {self.response_time_threshold}s"
                        )
                        
                except Exception as e:
                    errors.append(f"Tool discovery failed: {e}")
                    
            # Get connection info
            try:
                connection_info = self.adapter.get_connection_info()
                details["connection_info"] = connection_info
            except Exception as e:
                errors.append(f"Failed to get connection info: {e}")
                
            # Determine overall status
            if not errors:
                status = "healthy"
            elif is_connected and tools_available > 0:
                status = "degraded"
            else:
                status = "unhealthy"
                
        except Exception as e:
            errors.append(f"Health check failed: {e}")
            status = "unhealthy"
            
        duration_ms = (time.time() - start_time) * 1000
        
        result = HealthCheckResult(
            status=status,
            timestamp=timestamp,
            duration_ms=duration_ms,
            details=details,
            errors=errors
        )
        
        self._last_health_check = result
        
        logger.info(
            f"Health check completed: {status}",
            extra={
                "status": status,
                "duration_ms": duration_ms,
                "errors_count": len(errors),
                "tools_available": details.get("tools_available", 0)
            }
        )
        
        return result
        
    def get_metrics(self) -> Dict[str, Any]:
        """Return current performance and usage metrics.
        
        Returns:
            Dictionary with comprehensive metrics
        """
        current_time = time.time()
        uptime = current_time - self._start_time
        
        # Get adapter metrics
        try:
            adapter_metrics = self.adapter.get_metrics()
        except Exception as e:
            logger.warning(f"Failed to get adapter metrics: {e}")
            adapter_metrics = {}
            
        # Build comprehensive metrics
        metrics = {
            "monitor": {
                "uptime_seconds": uptime,
                "monitoring_active": self._monitoring_active,
                "check_interval": self.check_interval,
                "last_check_timestamp": self._last_health_check.timestamp if self._last_health_check else None,
                "metric_history_size": len(self._metric_history)
            },
            "adapter": adapter_metrics,
            "health": {
                "status": self._last_health_check.status if self._last_health_check else "unknown",
                "errors": self._last_health_check.errors if self._last_health_check else [],
                "last_check_duration_ms": self._last_health_check.duration_ms if self._last_health_check else None
            },
            "thresholds": {
                "error_rate_threshold": self.error_rate_threshold,
                "response_time_threshold": self.response_time_threshold
            }
        }
        
        return metrics
        
    def get_metric_history(self, limit: Optional[int] = None) -> List[MetricSnapshot]:
        """Get historical metric snapshots.
        
        Args:
            limit: Maximum number of snapshots to return (None for all)
            
        Returns:
            List of MetricSnapshot objects, newest first
        """
        history = list(reversed(self._metric_history))  # Newest first
        
        if limit:
            history = history[:limit]
            
        return history
        
    def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of current health status.
        
        Returns:
            Health summary dictionary
        """
        if not self._last_health_check:
            return {
                "status": "unknown",
                "message": "No health check performed yet",
                "timestamp": None
            }
            
        check = self._last_health_check
        
        # Create human-readable message
        if check.status == "healthy":
            message = "All systems operational"
        elif check.status == "degraded":
            message = f"Operational with issues: {', '.join(check.errors)}"
        else:
            message = f"System unhealthy: {', '.join(check.errors)}"
            
        return {
            "status": check.status,
            "message": message,
            "timestamp": check.timestamp,
            "duration_ms": check.duration_ms,
            "tools_available": check.details.get("tools_available", 0),
            "connected": check.details.get("connected", False),
            "error_count": len(check.errors)
        }
        
    async def start_monitoring(self) -> None:
        """Start automatic health monitoring.
        
        Raises:
            RuntimeError: If monitoring is already active
        """
        if self._monitoring_active:
            raise RuntimeError("Monitoring is already active")
            
        logger.info(f"Starting automatic health monitoring (interval: {self.check_interval}s)")
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
    async def stop_monitoring(self) -> None:
        """Stop automatic health monitoring."""
        if not self._monitoring_active:
            return
            
        logger.info("Stopping automatic health monitoring")
        
        self._monitoring_active = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            finally:
                self._monitoring_task = None
                
    async def _monitoring_loop(self) -> None:
        """Internal monitoring loop."""
        while self._monitoring_active:
            try:
                # Perform health check
                await self.health_check()
                
                # Capture metric snapshot
                self._capture_metric_snapshot()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                
            try:
                # Wait for next check
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
                
        logger.debug("Monitoring loop terminated")
        
    def _capture_metric_snapshot(self) -> None:
        """Capture current metrics as a snapshot."""
        try:
            current_metrics = self.adapter.get_metrics()
            connection_info = self.adapter.get_connection_info()
            
            snapshot = MetricSnapshot(
                timestamp=time.time(),
                uptime_seconds=current_metrics.get("uptime_seconds", 0),
                total_requests=current_metrics.get("total_requests", 0),
                total_errors=current_metrics.get("total_errors", 0),
                error_rate=current_metrics.get("error_rate", 0.0),
                connected=current_metrics.get("connected", False),
                tools_available=0,  # Will be updated if health check includes tool count
                connection_info=connection_info
            )
            
            # Add tools available if we have a recent health check
            if (self._last_health_check and 
                self._last_health_check.details and 
                "tools_available" in self._last_health_check.details):
                snapshot.tools_available = self._last_health_check.details["tools_available"]
                
            # Add to history
            self._metric_history.append(snapshot)
            
            # Trim history if it gets too large
            if len(self._metric_history) > self._max_history_size:
                self._metric_history = self._metric_history[-self._max_history_size:]
                
        except Exception as e:
            logger.warning(f"Failed to capture metric snapshot: {e}")
            
    def reset_metrics(self) -> None:
        """Reset metrics history and counters."""
        logger.info("Resetting health monitor metrics")
        
        self._metric_history.clear()
        self._last_health_check = None
        self._start_time = time.time()
        
    @property
    def is_monitoring(self) -> bool:
        """Check if automatic monitoring is active."""
        return self._monitoring_active
        
    @property
    def last_health_check(self) -> Optional[HealthCheckResult]:
        """Get the last health check result."""
        return self._last_health_check


class HealthCheckRegistry:
    """Registry for managing multiple health monitors."""
    
    def __init__(self):
        """Initialize health check registry."""
        self._monitors: Dict[str, MCPHealthMonitor] = {}
        
    def register(self, name: str, monitor: MCPHealthMonitor) -> None:
        """Register a health monitor.
        
        Args:
            name: Unique name for the monitor
            monitor: Health monitor instance
        """
        self._monitors[name] = monitor
        logger.info(f"Registered health monitor: {name}")
        
    def unregister(self, name: str) -> None:
        """Unregister a health monitor.
        
        Args:
            name: Name of monitor to unregister
        """
        if name in self._monitors:
            del self._monitors[name]
            logger.info(f"Unregistered health monitor: {name}")
            
    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """Perform health checks on all registered monitors.
        
        Returns:
            Dictionary mapping monitor names to health check results
        """
        results = {}
        
        for name, monitor in self._monitors.items():
            try:
                result = await monitor.health_check()
                results[name] = result
            except Exception as e:
                results[name] = HealthCheckResult(
                    status="unhealthy",
                    timestamp=time.time(),
                    duration_ms=0.0,
                    errors=[f"Health check failed: {e}"]
                )
                
        return results
        
    def get_all_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get health summaries for all registered monitors.
        
        Returns:
            Dictionary mapping monitor names to health summaries
        """
        summaries = {}
        
        for name, monitor in self._monitors.items():
            summaries[name] = monitor.get_health_summary()
            
        return summaries
        
    async def start_all_monitoring(self) -> None:
        """Start monitoring for all registered monitors."""
        for name, monitor in self._monitors.items():
            try:
                if not monitor.is_monitoring:
                    await monitor.start_monitoring()
                    logger.info(f"Started monitoring for: {name}")
            except Exception as e:
                logger.error(f"Failed to start monitoring for {name}: {e}")
                
    async def stop_all_monitoring(self) -> None:
        """Stop monitoring for all registered monitors."""
        for name, monitor in self._monitors.items():
            try:
                if monitor.is_monitoring:
                    await monitor.stop_monitoring()
                    logger.info(f"Stopped monitoring for: {name}")
            except Exception as e:
                logger.error(f"Failed to stop monitoring for {name}: {e}")
                
    @property
    def monitor_count(self) -> int:
        """Get count of registered monitors."""
        return len(self._monitors)
        
    def list_monitors(self) -> List[str]:
        """Get list of registered monitor names."""
        return list(self._monitors.keys())