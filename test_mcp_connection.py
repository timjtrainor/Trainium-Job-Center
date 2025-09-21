#!/usr/bin/env python3
"""
Test script for MCP Gateway connection with proper sessionid handling.

This script demonstrates the corrected SSE connection process that:
1. Connects to the MCP Gateway
2. Properly follows redirects with sessionid parameters
3. Lists available tools from connected servers
"""

import asyncio
import sys
from pathlib import Path

# Add the python-service to the path
sys.path.insert(0, str(Path(__file__).parent / "python-service"))

from app.services.mcp_adapter import MCPServerAdapter


async def test_mcp_connection():
    """Test MCP connection with proper sessionid handling."""
    
    print("🔍 Testing MCP Gateway Connection with Proper SessionID Handling")
    print("=" * 70)
    
    # Use the Docker MCP Gateway URL that the service uses
    gateway_url = "http://mcp-gateway:8811"  # Docker internal URL
    # gateway_url = "http://localhost:8811"  # For local testing
    
    print(f"Gateway URL: {gateway_url}")
    print()
    
    adapter = MCPServerAdapter(gateway_url)
    
    try:
        print("📡 Connecting to MCP Gateway...")
        await adapter.connect()
        
        print("✅ Successfully connected to MCP Gateway!")
        print()
        
        # List connected servers
        servers = adapter.get_available_servers()
        print(f"🖥️  Connected servers: {servers}")
        print()
        
        # List all available tools
        tools = adapter.get_available_tools()
        print(f"🔧 Total tools available: {len(tools)}")
        print()
        
        if tools:
            print("📋 Available Tools:")
            print("-" * 50)
            for tool_name, tool_config in tools.items():
                server = tool_config.get('server', 'unknown')
                description = tool_config.get('description', 'No description')
                print(f"  • {tool_name}")
                print(f"    Server: {server}")
                print(f"    Description: {description}")
                print()
        
        # Test LinkedIn-specific tools
        linkedin_tools = adapter.get_linkedin_tools()
        print(f"🔗 LinkedIn tools: {len(linkedin_tools)}")
        if linkedin_tools:
            for tool in linkedin_tools:
                print(f"  • {tool['name']}: {tool['description']}")
        
        # Test DuckDuckGo tools
        duckduckgo_tools = adapter.get_duckduckgo_tools()
        print(f"🦆 DuckDuckGo tools: {len(duckduckgo_tools)}")
        if duckduckgo_tools:
            for tool in duckduckgo_tools:
                print(f"  • {tool['name']}: {tool['description']}")
        
        # Test tool execution (optional - only if tools are available)
        if tools:
            print("\n🧪 Testing Tool Execution...")
            
            # Try to execute the first available tool with minimal args
            first_tool_name = list(tools.keys())[0]
            print(f"Testing tool: {first_tool_name}")
            
            try:
                # This is just a connection test - we won't provide real arguments
                result = await adapter.call_tool(first_tool_name, test=True)
                print(f"Tool execution result: {result[:100]}...")  # Truncate long results
            except Exception as e:
                print(f"Tool execution test failed (expected): {e}")
        
        print("\n✅ MCP Connection Test Completed Successfully!")
        
    except Exception as e:
        print(f"❌ MCP Connection Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        print("\n🔌 Disconnecting from MCP Gateway...")
        await adapter.disconnect()
        print("✅ Disconnected successfully!")
    
    return True


async def test_specific_connection(server_name: str = "duckduckgo"):
    """Test connection to a specific server with detailed logging."""
    
    print(f"\n🎯 Testing Specific Connection to: {server_name}")
    print("=" * 50)
    
    gateway_url = "http://mcp-gateway:8811"
    
    import httpx
    from urllib.parse import urljoin
    
    async with httpx.AsyncClient(follow_redirects=False, timeout=10.0) as session:
        try:
            print(f"📞 POST {gateway_url}/servers/{server_name}/connect")
            
            response = await session.post(f"{gateway_url}/servers/{server_name}/connect")
            
            print(f"📨 Response Status: {response.status_code}")
            print(f"📨 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 307:
                location = response.headers.get("location")
                redirect_url = urljoin(f"{gateway_url}/", location)
                print(f"🔀 Redirect URL: {redirect_url}")
                
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(redirect_url)
                query_params = parse_qs(parsed.query)
                session_id = query_params.get("sessionid", [None])[0]
                
                print(f"🆔 Extracted Session ID: {session_id}")
                
                if session_id:
                    print("✅ Session ID found in redirect URL!")
                else:
                    print("❌ No session ID found in redirect URL!")
                    
            elif response.status_code == 200:
                try:
                    payload = response.json()
                    endpoint = payload.get("endpoint")
                    print(f"📍 JSON Endpoint: {endpoint}")
                    
                    if endpoint and "sessionid" in endpoint:
                        print("✅ Session ID found in JSON endpoint!")
                    else:
                        print("❌ No session ID found in JSON endpoint!")
                        
                except Exception as e:
                    print(f"❌ Failed to parse JSON response: {e}")
            else:
                print(f"❌ Unexpected response status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")


if __name__ == "__main__":
    print("🚀 MCP Connection Test Suite")
    print("=" * 70)
    
    # Run the main test
    success = asyncio.run(test_mcp_connection())
    
    # Run specific connection test
    asyncio.run(test_specific_connection("duckduckgo"))
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)