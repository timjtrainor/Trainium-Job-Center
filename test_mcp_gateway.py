#!/usr/bin/env python3
"""
Test script for MCP Gateway endpoints

This script tests the MCP Gateway implementation by making HTTP requests
to the various MCP protocol endpoints.
"""

import json
import asyncio
import aiohttp
import sys
from typing import Dict, Any

class MCPGatewayTester:
    """Test client for MCP Gateway endpoints."""
    
    def __init__(self, gateway_url: str = "http://localhost:8811"):
        self.gateway_url = gateway_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        try:
            async with self.session.get(f"{self.gateway_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data.get('status')}")
                    print(f"   Gateway version: {data.get('version')}")
                    print(f"   Transport: {data.get('transport')}")
                    print(f"   Servers: {data.get('servers')}")
                    return True
                else:
                    print(f"❌ Health check failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_initialize(self) -> bool:
        """Test the MCP initialize endpoint."""
        try:
            request_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            async with self.session.post(
                f"{self.gateway_url}/mcp/initialize",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Initialize request passed")
                    print(f"   Protocol version: {data.get('result', {}).get('protocolVersion')}")
                    print(f"   Server info: {data.get('result', {}).get('serverInfo', {}).get('name')}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Initialize failed: HTTP {response.status}")
                    print(f"   Response: {text}")
                    return False
        except Exception as e:
            print(f"❌ Initialize error: {e}")
            return False
    
    async def test_tools_list(self) -> bool:
        """Test the tools list endpoint."""
        try:
            request_data = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            async with self.session.post(
                f"{self.gateway_url}/mcp/tools/list",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tools = data.get('result', {}).get('tools', [])
                    print(f"✅ Tools list request passed")
                    print(f"   Available tools: {len(tools)}")
                    for tool in tools:
                        print(f"   - {tool.get('name')}: {tool.get('description')}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Tools list failed: HTTP {response.status}")
                    print(f"   Response: {text}")
                    return False
        except Exception as e:
            print(f"❌ Tools list error: {e}")
            return False
    
    async def test_tool_call(self) -> bool:
        """Test calling a tool through the gateway."""
        try:
            request_data = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "duckduckgo_search",
                    "arguments": {
                        "query": "Python MCP protocol"
                    }
                }
            }
            
            async with self.session.post(
                f"{self.gateway_url}/mcp/tools/call",
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('result', {}).get('content', [])
                    print(f"✅ Tool call request passed")
                    if content:
                        print(f"   Result: {content[0].get('text', '')[:100]}...")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Tool call failed: HTTP {response.status}")
                    print(f"   Response: {text}")
                    return False
        except Exception as e:
            print(f"❌ Tool call error: {e}")
            return False
    
    async def test_gateway_status(self) -> bool:
        """Test the gateway status endpoint."""
        try:
            async with self.session.get(f"{self.gateway_url}/mcp/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Gateway status request passed")
                    print(f"   Gateway status: {data.get('gateway', {}).get('status')}")
                    print(f"   Active connections: {data.get('active_connections')}")
                    return True
                else:
                    print(f"❌ Gateway status failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Gateway status error: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all test cases."""
        print("🚀 Starting MCP Gateway tests...\n")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Initialize", self.test_initialize),
            ("Tools List", self.test_tools_list),
            ("Tool Call", self.test_tool_call),
            ("Gateway Status", self.test_gateway_status),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n--- Testing {test_name} ---")
            result = await test_func()
            results.append(result)
        
        passed = sum(results)
        total = len(results)
        
        print(f"\n🏁 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All tests passed! MCP Gateway is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the gateway implementation.")
            return False


async def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MCP Gateway endpoints")
    parser.add_argument(
        "--url",
        default="http://localhost:8811",
        help="MCP Gateway URL (default: http://localhost:8811)"
    )
    
    args = parser.parse_args()
    
    try:
        async with MCPGatewayTester(args.url) as tester:
            success = await tester.run_all_tests()
            sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())