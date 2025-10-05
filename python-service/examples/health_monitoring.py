#!/usr/bin/env python3
"""Health Monitoring Example.

This example demonstrates health monitoring and metrics collection for MCP 
Gateway integration, including:
- Connection health checks
- Performance metrics
- System monitoring
- Alert patterns
- Dashboard-style reporting
"""

import asyncio
import sys
import json
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.mcp import (
    MCPGatewayAdapter,
    MCPConfig,
    StreamingTransport,
    MCPHealthMonitor,
    HealthCheckResult,
    MetricSnapshot,
    ConnectionError,
    MCPToolFactory
)


async def basic_health_monitoring():
    """Demonstrate basic health monitoring capabilities."""
    print("🏥 Basic Health Monitoring")
    print("=" * 35)
    
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    
    # Create health monitor
    health_monitor = MCPHealthMonitor(adapter)
    
    print("\n📊 Adapter Health Information:")
    
    # Get basic connection info
    connection_info = adapter.get_connection_info()
    for key, value in connection_info.items():
        status_icon = "✓" if key != "connected" or value else "❌"
        print(f"  {status_icon} {key}: {value}")
    
    # Try to perform health check
    print("\n🔍 Performing Health Check:")
    try:
        async with adapter:
            health_result = await health_monitor.check_health()
            print(f"  Overall Status: {'✓ Healthy' if health_result.is_healthy else '❌ Unhealthy'}")
            print(f"  Response Time: {health_result.response_time:.3f}s")
            print(f"  Timestamp: {health_result.timestamp}")
            
            if health_result.details:
                print("  Details:")
                for key, value in health_result.details.items():
                    print(f"    - {key}: {value}")
            
            if health_result.errors:
                print("  Errors:")
                for error in health_result.errors:
                    print(f"    - {error}")
                    
    except ConnectionError:
        print("  ❌ Health check failed - Gateway unavailable")
        print("  💡 This is expected if the MCP Gateway is not running")


async def performance_metrics_monitoring():
    """Demonstrate performance metrics collection."""
    print("\n📈 Performance Metrics Monitoring")
    print("=" * 40)
    
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    health_monitor = MCPHealthMonitor(adapter)
    
    try:
        async with adapter:
            print("✓ Connected for performance monitoring")
            
            # Collect baseline metrics
            print("\n📊 Collecting Performance Metrics...")
            
            # Measure tool discovery performance
            start_time = time.time()
            try:
                tools = await adapter.list_tools()
                discovery_time = time.time() - start_time
                print(f"  📋 Tool Discovery: {discovery_time:.3f}s ({len(tools)} tools)")
            except Exception as e:
                print(f"  ❌ Tool Discovery Failed: {e}")
                discovery_time = None
            
            # Measure tool execution performance (if tools available)
            if tools:
                tool_name = list(tools.keys())[0]
                print(f"\n⚡ Testing Tool Performance: {tool_name}")
                
                execution_times = []
                for i in range(3):  # Test multiple executions
                    start_time = time.time()
                    try:
                        # Create minimal valid arguments
                        tool_schema = tools[tool_name].get("inputSchema", {})
                        properties = tool_schema.get("properties", {})
                        args = {}
                        
                        # Add required string parameters
                        for prop_name, prop_info in properties.items():
                            if prop_info.get("type") == "string":
                                args[prop_name] = "test query"
                                break
                        
                        result = await adapter.execute_tool(tool_name, args)
                        execution_time = time.time() - start_time
                        execution_times.append(execution_time)
                        print(f"    Execution {i+1}: {execution_time:.3f}s")
                        
                    except Exception as e:
                        print(f"    Execution {i+1} failed: {e}")
                
                if execution_times:
                    avg_time = sum(execution_times) / len(execution_times)
                    min_time = min(execution_times)
                    max_time = max(execution_times)
                    print(f"  📊 Performance Summary:")
                    print(f"    Average: {avg_time:.3f}s")
                    print(f"    Min: {min_time:.3f}s")
                    print(f"    Max: {max_time:.3f}s")
            
            # Get system metrics snapshot
            print("\n💾 System Metrics Snapshot:")
            try:
                metrics = await health_monitor.get_metrics()
                if metrics:
                    print(f"  🕒 Uptime: {metrics.uptime:.1f}s")
                    print(f"  📊 Request Count: {metrics.request_count}")
                    print(f"  ❌ Error Count: {metrics.error_count}")
                    print(f"  📈 Success Rate: {metrics.success_rate:.1%}")
                    print(f"  ⏱️  Avg Response Time: {metrics.avg_response_time:.3f}s")
                else:
                    print("  ℹ️  No metrics available")
            except Exception as e:
                print(f"  ❌ Metrics collection failed: {e}")
    
    except ConnectionError:
        print("ℹ️  Gateway not available for performance monitoring")


async def continuous_monitoring_demo():
    """Demonstrate continuous monitoring with alerts."""
    print("\n🔄 Continuous Monitoring Demo")
    print("=" * 35)
    
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    health_monitor = MCPHealthMonitor(adapter)
    
    # Monitoring configuration
    monitoring_duration = 10  # seconds
    check_interval = 2  # seconds
    response_time_threshold = 1.0  # seconds
    
    print(f"🕒 Monitoring for {monitoring_duration} seconds (checks every {check_interval}s)")
    print(f"⚠️  Alert threshold: {response_time_threshold}s response time")
    
    health_history = []
    alerts = []
    
    start_time = time.time()
    
    try:
        async with adapter:
            while time.time() - start_time < monitoring_duration:
                # Perform health check
                try:
                    health_result = await health_monitor.check_health()
                    health_history.append(health_result)
                    
                    # Check for alerts
                    if health_result.response_time > response_time_threshold:
                        alert = {
                            "timestamp": health_result.timestamp,
                            "type": "slow_response",
                            "message": f"Slow response time: {health_result.response_time:.3f}s",
                            "severity": "warning"
                        }
                        alerts.append(alert)
                        print(f"  ⚠️  ALERT: {alert['message']}")
                    
                    if not health_result.is_healthy:
                        alert = {
                            "timestamp": health_result.timestamp,
                            "type": "unhealthy",
                            "message": "Health check failed",
                            "severity": "critical",
                            "errors": health_result.errors
                        }
                        alerts.append(alert)
                        print(f"  🚨 CRITICAL: {alert['message']}")
                    else:
                        print(f"  ✓ Healthy ({health_result.response_time:.3f}s)")
                        
                except Exception as e:
                    alert = {
                        "timestamp": datetime.now(),
                        "type": "check_failed",
                        "message": f"Health check failed: {e}",
                        "severity": "error"
                    }
                    alerts.append(alert)
                    print(f"  ❌ CHECK FAILED: {e}")
                
                # Wait before next check
                await asyncio.sleep(check_interval)
        
        # Generate monitoring report
        print(f"\n📋 Monitoring Report ({len(health_history)} checks)")
        print("=" * 30)
        
        if health_history:
            response_times = [h.response_time for h in health_history if h.response_time]
            if response_times:
                print(f"📊 Response Time Statistics:")
                print(f"  Average: {sum(response_times)/len(response_times):.3f}s")
                print(f"  Min: {min(response_times):.3f}s")
                print(f"  Max: {max(response_times):.3f}s")
            
            healthy_count = sum(1 for h in health_history if h.is_healthy)
            health_rate = healthy_count / len(health_history)
            print(f"🏥 Health Rate: {health_rate:.1%} ({healthy_count}/{len(health_history)})")
        
        if alerts:
            print(f"\n🚨 Alerts Generated: {len(alerts)}")
            for alert in alerts[-3:]:  # Show last 3 alerts
                severity_icon = {"warning": "⚠️", "critical": "🚨", "error": "❌"}.get(alert["severity"], "ℹ️")
                print(f"  {severity_icon} {alert['message']}")
        else:
            print("\n✅ No alerts generated - system healthy!")
    
    except ConnectionError:
        print("ℹ️  Gateway not available for continuous monitoring")


async def dashboard_style_monitoring():
    """Create a dashboard-style monitoring display."""
    print("\n📊 Dashboard-Style Monitoring")
    print("=" * 40)
    
    transport = StreamingTransport("http://localhost:8811")
    adapter = MCPGatewayAdapter(transport=transport)
    health_monitor = MCPHealthMonitor(adapter)
    
    try:
        async with adapter:
            # Collect comprehensive system information
            print("🔄 Collecting system information...")
            
            dashboard_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "connection": {},
                "tools": {},
                "performance": {},
                "health": {}
            }
            
            # Connection information
            connection_info = adapter.get_connection_info()
            dashboard_data["connection"] = connection_info
            
            # Tool information
            try:
                tools = await adapter.list_tools()
                dashboard_data["tools"] = {
                    "count": len(tools),
                    "names": list(tools.keys())[:5],  # First 5 tools
                    "total": len(tools)
                }
            except Exception as e:
                dashboard_data["tools"] = {"error": str(e)}
            
            # Health check
            try:
                health_result = await health_monitor.check_health()
                dashboard_data["health"] = {
                    "status": "healthy" if health_result.is_healthy else "unhealthy",
                    "response_time": health_result.response_time,
                    "errors": health_result.errors
                }
            except Exception as e:
                dashboard_data["health"] = {"error": str(e)}
            
            # Performance metrics
            try:
                metrics = await health_monitor.get_metrics()
                if metrics:
                    dashboard_data["performance"] = {
                        "uptime": metrics.uptime,
                        "requests": metrics.request_count,
                        "errors": metrics.error_count,
                        "success_rate": metrics.success_rate,
                        "avg_response_time": metrics.avg_response_time
                    }
            except Exception as e:
                dashboard_data["performance"] = {"error": str(e)}
            
            # Display dashboard
            print("\n" + "="*60)
            print("🎛️  MCP GATEWAY MONITORING DASHBOARD")
            print("="*60)
            
            # System status
            connection_status = "🟢 ONLINE" if dashboard_data["connection"].get("connected") else "🔴 OFFLINE"
            health_status = "🟢 HEALTHY" if dashboard_data["health"].get("status") == "healthy" else "🟡 DEGRADED"
            
            print(f"📊 SYSTEM STATUS: {connection_status}")
            print(f"🏥 HEALTH STATUS: {health_status}")
            print(f"🕒 LAST UPDATE: {dashboard_data['timestamp']}")
            print("-" * 60)
            
            # Connection details
            print("🔌 CONNECTION:")
            for key, value in dashboard_data["connection"].items():
                print(f"   {key}: {value}")
            print()
            
            # Tools summary
            print("🛠️  TOOLS:")
            if "error" in dashboard_data["tools"]:
                print(f"   Error: {dashboard_data['tools']['error']}")
            else:
                print(f"   Count: {dashboard_data['tools']['count']}")
                if dashboard_data['tools']['names']:
                    print(f"   Available: {', '.join(dashboard_data['tools']['names'])}")
                    if dashboard_data['tools']['total'] > 5:
                        print(f"   ... and {dashboard_data['tools']['total'] - 5} more")
            print()
            
            # Performance metrics
            print("📈 PERFORMANCE:")
            if "error" in dashboard_data["performance"]:
                print(f"   Error: {dashboard_data['performance']['error']}")
            else:
                perf = dashboard_data["performance"]
                print(f"   Uptime: {perf.get('uptime', 0):.1f}s")
                print(f"   Requests: {perf.get('requests', 0)}")
                print(f"   Success Rate: {perf.get('success_rate', 0):.1%}")
                print(f"   Avg Response: {perf.get('avg_response_time', 0):.3f}s")
            print()
            
            # Health details
            print("🏥 HEALTH:")
            if "error" in dashboard_data["health"]:
                print(f"   Error: {dashboard_data['health']['error']}")
            else:
                health = dashboard_data["health"]
                print(f"   Status: {health.get('status', 'unknown').upper()}")
                print(f"   Response Time: {health.get('response_time', 0):.3f}s")
                if health.get('errors'):
                    print(f"   Errors: {len(health['errors'])}")
            
            print("="*60)
            
            # Export dashboard data (for integration with monitoring systems)
            dashboard_json = json.dumps(dashboard_data, indent=2, default=str)
            print(f"\n💾 Dashboard data available as JSON ({len(dashboard_json)} chars)")
            print("   (Use this for integration with monitoring systems)")
    
    except ConnectionError:
        print("ℹ️  Gateway not available for dashboard monitoring")
        print("🎛️  Showing offline dashboard...")
        
        offline_dashboard = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "offline",
            "connection": {"connected": False, "error": "Gateway not available"}
        }
        
        print("\n" + "="*60)
        print("🎛️  MCP GATEWAY MONITORING DASHBOARD")  
        print("="*60)
        print("📊 SYSTEM STATUS: 🔴 OFFLINE")
        print(f"🕒 LAST UPDATE: {offline_dashboard['timestamp']}")
        print("💡 Start the MCP Gateway to see full monitoring data")
        print("="*60)


async def health_check_integration():
    """Demonstrate integration with existing health check systems."""
    print("\n🔗 Health Check Integration")
    print("=" * 35)
    
    async def kubernetes_health_check():
        """Example Kubernetes-style health check endpoint."""
        transport = StreamingTransport("http://localhost:8811")
        adapter = MCPGatewayAdapter(transport=transport, timeout=5)
        health_monitor = MCPHealthMonitor(adapter)
        
        try:
            async with adapter:
                health_result = await health_monitor.check_health()
                
                if health_result.is_healthy and health_result.response_time < 2.0:
                    return {"status": "healthy", "code": 200}
                else:
                    return {"status": "degraded", "code": 503, "details": health_result.errors}
                    
        except Exception as e:
            return {"status": "unhealthy", "code": 503, "error": str(e)}
    
    async def prometheus_metrics():
        """Example Prometheus-style metrics."""
        transport = StreamingTransport("http://localhost:8811")
        adapter = MCPGatewayAdapter(transport=transport)
        health_monitor = MCPHealthMonitor(adapter)
        
        metrics_output = []
        
        try:
            async with adapter:
                # Connection status metric
                connection_info = adapter.get_connection_info()
                connected = 1 if connection_info.get("connected") else 0
                metrics_output.append(f"mcp_gateway_connected {connected}")
                
                # Health check metrics  
                health_result = await health_monitor.check_health()
                healthy = 1 if health_result.is_healthy else 0
                metrics_output.append(f"mcp_gateway_healthy {healthy}")
                metrics_output.append(f"mcp_gateway_response_time {health_result.response_time}")
                
                # Tool count
                tools = await adapter.list_tools()
                metrics_output.append(f"mcp_gateway_tools_available {len(tools)}")
                
                # System metrics
                system_metrics = await health_monitor.get_metrics()
                if system_metrics:
                    metrics_output.append(f"mcp_gateway_requests_total {system_metrics.request_count}")
                    metrics_output.append(f"mcp_gateway_errors_total {system_metrics.error_count}")
                    metrics_output.append(f"mcp_gateway_uptime_seconds {system_metrics.uptime}")
                
        except Exception as e:
            metrics_output.append(f"mcp_gateway_connected 0")
            metrics_output.append(f"mcp_gateway_healthy 0")
        
        return "\n".join(metrics_output)
    
    # Demonstrate health check integrations
    print("\n🔍 Kubernetes-style Health Check:")
    k8s_result = await kubernetes_health_check()
    print(f"  Status: {k8s_result['status']}")
    print(f"  HTTP Code: {k8s_result['code']}")
    if 'error' in k8s_result:
        print(f"  Error: {k8s_result['error']}")
    
    print("\n📊 Prometheus-style Metrics:")
    prometheus_output = await prometheus_metrics()
    metrics_lines = prometheus_output.splitlines()
    for line in metrics_lines[:5]:  # Show first 5 metrics
        print(f"  {line}")
    if len(metrics_lines) > 5:
        print(f"  ... and {len(metrics_lines) - 5} more metrics")


async def main():
    """Run all health monitoring examples."""
    print("🏥 MCP Health Monitoring Examples")
    print("=" * 50)
    
    # Basic health monitoring
    await basic_health_monitoring()
    
    # Performance metrics
    await performance_metrics_monitoring()
    
    # Continuous monitoring
    await continuous_monitoring_demo()
    
    # Dashboard-style monitoring
    await dashboard_style_monitoring()
    
    # Health check integration
    await health_check_integration()
    
    print("\n✨ Health monitoring examples completed!")
    print("\nKey capabilities demonstrated:")
    print("1. Basic health checks and status reporting")
    print("2. Performance metrics collection and analysis")
    print("3. Continuous monitoring with alerting")
    print("4. Dashboard-style comprehensive reporting")
    print("5. Integration patterns for existing monitoring systems")


if __name__ == "__main__":
    asyncio.run(main())
