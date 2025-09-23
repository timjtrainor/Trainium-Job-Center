#!/usr/bin/env python3
"""
Integration test for MCP Protocol Implementation

This script demonstrates the complete MCP protocol flow including:
- Transport connection
- Protocol initialization handshake
- Session management
- Request/response cycles
"""

import asyncio
import json
import sys
from pathlib import Path

# Add python-service to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.mcp.mcp_protocol import MCPProtocol
from app.services.mcp.mcp_session import MCPSession, create_mcp_session
from app.services.mcp.mcp_transport import MCPTransport
from app.services.mcp.mcp_exceptions import MCPError


class MockGatewayTransport(MCPTransport):
    """Mock transport that simulates a real MCP Gateway."""
    
    def __init__(self):
        super().__init__()
        self.request_count = 0
        
    async def connect(self):
        print("🔌 Connecting to mock MCP Gateway...")
        await asyncio.sleep(0.1)  # Simulate connection time
        self._connected = True
        print("✅ Connected to mock MCP Gateway")
        
    async def disconnect(self):
        print("🔌 Disconnecting from mock MCP Gateway...")
        self._connected = False
        print("✅ Disconnected from mock MCP Gateway")
        
    async def send_message(self, message):
        print(f"📤 Sending: {json.dumps(message, indent=2)}")
        await asyncio.sleep(0.05)  # Simulate network delay
        
    async def receive_message(self):
        self.request_count += 1
        await asyncio.sleep(0.05)  # Simulate network delay
        
        # Simulate different responses based on method
        if self.request_count == 1:  # Initialize request
            response = {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "tools": {"listChanged": True, "subscribe": False},
                        "resources": {"listChanged": True, "subscribe": True},
                        "prompts": {"listChanged": False}
                    },
                    "serverInfo": {
                        "name": "trainium-mcp-gateway", 
                        "version": "1.0.0"
                    },
                    "instructions": "Connected to Trainium MCP Gateway"
                }
            }
        elif self.request_count == 2:  # Tools list request
            response = {
                "jsonrpc": "2.0",
                "id": 2,
                "result": {
                    "tools": [
                        {
                            "name": "duckduckgo_search",
                            "description": "Search the web using DuckDuckGo",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Search query"}
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "linkedin_search", 
                            "description": "Search LinkedIn for job opportunities",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "keywords": {"type": "string", "description": "Job search keywords"},
                                    "location": {"type": "string", "description": "Job location"}
                                },
                                "required": ["keywords"]
                            }
                        },
                        {
                            "name": "get_recommended_jobs",
                            "description": "Get personalized job recommendations for the current LinkedIn user",
                            "inputSchema": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        },
                        {
                            "name": "get_job_details",
                            "description": "Get detailed information for a specific LinkedIn job posting",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "job_id": {"type": "string", "description": "LinkedIn job ID"}
                                },
                                "required": ["job_id"]
                            }
                        }
                    ]
                }
            }
        elif self.request_count == 3:  # Tool call request
            # Determine which tool was called based on request data (this is simplified)
            # In a real implementation, we'd parse the tool name from the request
            response = {
                "jsonrpc": "2.0",
                "id": 3,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Mock search results for 'Python MCP protocol': Found 5 relevant results about Model Context Protocol implementation in Python..."
                        }
                    ]
                }
            }
        else:  # Shutdown (no response expected)
            return {"jsonrpc": "2.0", "id": self.request_count, "result": {}}
            
        print(f"📥 Receiving: {json.dumps(response, indent=2)}")
        return response


async def test_protocol_directly():
    """Test MCP protocol handler directly."""
    print("\n🧪 Testing MCP Protocol Handler Directly")
    print("=" * 50)
    
    transport = MockGatewayTransport()
    protocol = MCPProtocol(transport, timeout=5)
    
    try:
        # Connect transport
        await transport.connect()
        
        # Test initialization
        print("\n1️⃣ Testing Protocol Initialization...")
        init_result = await protocol.initialize()
        print(f"✅ Initialization successful!")
        print(f"   Protocol Version: {init_result['protocolVersion']}")
        print(f"   Server: {init_result['serverInfo']['name']} v{init_result['serverInfo']['version']}")
        print(f"   Capabilities: {list(init_result['capabilities'].keys())}")
        
        # Test capability checking
        print(f"\n2️⃣ Testing Capability Negotiation...")
        assert protocol.has_capability("tools"), "Should have tools capability"
        assert protocol.has_capability("resources"), "Should have resources capability" 
        assert not protocol.has_capability("nonexistent"), "Should not have nonexistent capability"
        print(f"✅ Capability checks passed!")
        
        tools_details = protocol.get_capability_details("tools")
        print(f"   Tools capability: {tools_details}")
        
        # Test request/response
        print(f"\n3️⃣ Testing Request/Response...")
        tools_result = await protocol.send_request("tools/list")
        print(f"✅ Tools list request successful!")
        print(f"   Found {len(tools_result['tools'])} tools:")
        for tool in tools_result['tools']:
            print(f"   - {tool['name']}: {tool['description']}")
            
        # Test tool call
        call_result = await protocol.send_request("tools/call", {
            "name": "duckduckgo_search",
            "arguments": {"query": "Python MCP protocol"}
        })
        print(f"✅ Tool call request successful!")
        content = call_result['content'][0]['text']
        print(f"   Result: {content[:100]}...")
        
        # Test shutdown
        print(f"\n4️⃣ Testing Graceful Shutdown...")
        await protocol.shutdown()
        print(f"✅ Shutdown successful!")
        
        await transport.disconnect()
        
    except Exception as e:
        print(f"❌ Protocol test failed: {e}")
        raise


async def test_session_manager():
    """Test MCP session management."""
    print("\n🧪 Testing MCP Session Manager")
    print("=" * 50)
    
    transport = MockGatewayTransport()
    protocol = MCPProtocol(transport, timeout=5)
    
    try:
        print("\n1️⃣ Testing Session Context Manager...")
        async with MCPSession(protocol) as session:
            print(f"✅ Session established!")
            print(f"   Active: {session.is_active}")
            print(f"   Capabilities: {list(session.server_capabilities.keys())}")
            
            # Test session info
            info = session.session_info
            print(f"   Session Info: {info['active']} | {info['initialized']} | {info['connected']}")
            
            # Test capability check through session
            assert session.has_capability("tools"), "Session should have tools capability"
            print(f"✅ Session capability check passed!")
            
            # Test request through session
            result = await session.send_request("tools/list")
            print(f"✅ Session request successful - found {len(result['tools'])} tools")
            
        print(f"✅ Session cleanup completed!")
        
    except Exception as e:
        print(f"❌ Session test failed: {e}")
        raise


async def test_convenience_function():
    """Test convenience session creation function."""
    print("\n🧪 Testing Convenience Session Creation")
    print("=" * 50)
    
    transport = MockGatewayTransport()
    
    try:
        print("\n1️⃣ Testing create_mcp_session convenience function...")
        async with create_mcp_session(transport, timeout=5) as session:
            print(f"✅ Convenience session created!")
            print(f"   Session type: {type(session).__name__}")
            print(f"   Active: {session.is_active}")
            
            # Quick capability test
            has_tools = session.has_capability("tools")
            print(f"   Has tools capability: {has_tools}")
            
            # Quick request test
            result = await session.send_request("tools/call", {
                "name": "linkedin_search",
                "arguments": {"keywords": "Python developer", "location": "San Francisco"}
            })
            print(f"✅ Convenience session request successful!")
            
        print(f"✅ Convenience session cleanup completed!")
        
    except Exception as e:
        print(f"❌ Convenience function test failed: {e}")
        raise


async def main():
    """Run all integration tests."""
    print("🚀 MCP Protocol Phase 2 Integration Tests")
    print("=" * 60)
    
    try:
        await test_protocol_directly()
        await test_session_manager() 
        await test_convenience_function()
        
        print(f"\n🎉 All integration tests passed!")
        print(f"✅ MCP Protocol Phase 2 implementation is working correctly!")
        
    except Exception as e:
        print(f"\n💥 Integration tests failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())