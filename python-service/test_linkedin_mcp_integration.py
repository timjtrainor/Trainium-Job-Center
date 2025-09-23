#!/usr/bin/env python3
"""
Test LinkedIn Recommended Jobs MCP Integration

This script validates that the LinkedIn recommended jobs crew properly
integrates with the existing MCP functionality.
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import patch

import httpx

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

print("🔍 LinkedIn Recommended Jobs MCP Integration Test")
print("=" * 55)

def test_mcp_imports():
    """Test that MCP components can be imported."""
    print("\n1️⃣ Testing MCP Import Integration...")
    
    try:
        from app.services.mcp import MCPConfig, MCPToolFactory, MCPToolWrapper
        print("✅ MCP core components imported successfully")
        
        # Test that the crew imports MCP correctly
        from app.services.crewai.linkedin_recommended_jobs.crew import _get_shared_mcp_factory
        print("✅ LinkedIn crew MCP factory function available")
        
        # Test that it follows same pattern as working crew
        from app.services.crewai.linkedin_job_search.crew import _get_shared_mcp_factory as existing_factory
        print("✅ Same MCP factory pattern as existing LinkedIn job search crew")
        
        return True
    except Exception as e:
        print(f"❌ MCP import test failed: {e}")
        return False

def test_crew_structure():
    """Test that the crew follows MCP integration patterns."""
    print("\n2️⃣ Testing Crew MCP Integration Structure...")
    
    try:
        # Test that crew file has the right MCP tool mapping
        with open("app/services/crewai/linkedin_recommended_jobs/crew.py", "r") as f:
            crew_content = f.read()
        
        # Check for MCP imports
        if "from app.services.mcp import MCPConfig, MCPToolFactory, MCPToolWrapper" in crew_content:
            print("✅ Crew imports from app.services.mcp (correct path)")
        else:
            print("❌ Crew missing proper MCP imports")
            return False
        
        # Check for required LinkedIn tools
        if "get_recommended_jobs" in crew_content:
            print("✅ Crew references get_recommended_jobs MCP tool")
        else:
            print("❌ Crew missing get_recommended_jobs tool")
            return False
            
        if "get_job_details" in crew_content:
            print("✅ Crew references get_job_details MCP tool")
        else:
            print("❌ Crew missing get_job_details tool")
            return False
        
        # Check for MCP tool factory usage
        if "_get_shared_mcp_factory" in crew_content:
            print("✅ Crew uses MCP factory pattern")
        else:
            print("❌ Crew missing MCP factory pattern")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Crew structure test failed: {e}")
        return False

def test_agent_tool_mapping():
    """Test that agents are properly mapped to MCP tools."""
    print("\n3️⃣ Testing Agent MCP Tool Mapping...")
    
    try:
        with open("app/services/crewai/linkedin_recommended_jobs/crew.py", "r") as f:
            crew_content = f.read()
        
        # Check that job collector agent gets get_recommended_jobs tool
        tool_mapping_section = None
        lines = crew_content.split('\n')
        for i, line in enumerate(lines):
            if "_DEFAULT_AGENT_TOOL_MAPPING" in line:
                # Get the next several lines that define the mapping
                mapping_lines = []
                j = i
                while j < len(lines) and not lines[j].strip().endswith('}'):
                    mapping_lines.append(lines[j])
                    j += 1
                if j < len(lines):
                    mapping_lines.append(lines[j])  # Include the closing }
                tool_mapping_section = '\n'.join(mapping_lines)
                break
        
        if tool_mapping_section:
            if "job_collector_agent" in tool_mapping_section and "get_recommended_jobs" in tool_mapping_section:
                print("✅ Job collector agent mapped to get_recommended_jobs tool")
            else:
                print("❌ Job collector agent not properly mapped")
                return False
                
            if "job_details_agent" in tool_mapping_section and "get_job_details" in tool_mapping_section:
                print("✅ Job details agent mapped to get_job_details tool")
            else:
                print("❌ Job details agent not properly mapped")
                return False
        else:
            print("❌ Could not find agent tool mapping")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Agent tool mapping test failed: {e}")
        return False

def test_service_integration():
    """Test that service layer properly integrates with crew."""
    print("\n4️⃣ Testing Service Layer MCP Integration...")
    
    try:
        with open("app/services/linkedin_recommended_jobs_service.py", "r") as f:
            service_content = f.read()
        
        # Check that service imports crew function
        if "from .crewai.linkedin_recommended_jobs import run_linkedin_recommended_jobs" in service_content:
            print("✅ Service imports crew function correctly")
        else:
            print("❌ Service missing crew import")
            return False
            
        # Check that service calls crew
        if "run_linkedin_recommended_jobs()" in service_content:
            print("✅ Service calls LinkedIn recommended jobs crew")
        else:
            print("❌ Service doesn't call crew")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Service integration test failed: {e}")
        return False

def test_api_endpoint():
    """Test that API endpoint is properly integrated."""
    print("\n5️⃣ Testing API Endpoint Integration...")
    
    try:
        with open("app/api/v1/endpoints/linkedin_recommended_jobs.py", "r") as f:
            endpoint_content = f.read()
        
        # Check service import
        if "from ....services.linkedin_recommended_jobs_service import fetch_linkedin_recommended_jobs" in endpoint_content:
            print("✅ API endpoint imports service correctly")
        else:
            print("❌ API endpoint missing service import")
            return False
            
        # Check router registration
        with open("app/api/router.py", "r") as f:
            router_content = f.read()
            
        if "from .v1.endpoints.linkedin_recommended_jobs import router as linkedin_recommended_jobs_router" in router_content:
            print("✅ API router imports LinkedIn recommended jobs endpoint")
        else:
            print("❌ API router missing endpoint import")
            return False
            
        if "api_router.include_router(linkedin_recommended_jobs_router" in router_content:
            print("✅ API router registers LinkedIn recommended jobs endpoint")
        else:
            print("❌ API router doesn't register endpoint")
            return False
            
        return True
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False


def test_streaming_transport_tool_population():
    """Validate that the streaming transport hydrates LinkedIn MCP tools."""
    print("\n6️⃣ Testing StreamingTransport MCP Tool Population...")

    env_backup = {
        "MCP_GATEWAY_URL": os.environ.get("MCP_GATEWAY_URL"),
        "MCP_GATEWAY_TRANSPORT": os.environ.get("MCP_GATEWAY_TRANSPORT"),
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
    }

    if env_backup["DATABASE_URL"] is None:
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

    os.environ["MCP_GATEWAY_TRANSPORT"] = "streaming"
    os.environ["MCP_GATEWAY_URL"] = "http://mock-mcp.local"

    def _mock_send(request: httpx.Request) -> httpx.Response:
        try:
            payload = json.loads(request.content.decode("utf-8")) if request.content else {}
        except json.JSONDecodeError:
            payload = {}

        path = request.url.path

        if path == "/mcp/initialize":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "result": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {"listChanged": True},
                        },
                        "serverInfo": {"name": "mock-mcp", "version": "1.0.0"},
                        "instructions": "Mock MCP gateway ready",
                    },
                },
            )

        if path == "/mcp/tools/list":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "get_recommended_jobs",
                                "description": "Fetch personalized LinkedIn job recommendations",
                                "inputSchema": {"type": "object", "properties": {}, "required": []},
                            },
                            {
                                "name": "get_job_details",
                                "description": "Fetch LinkedIn job posting details",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "job_id": {
                                            "type": "string",
                                            "description": "LinkedIn job identifier",
                                        }
                                    },
                                    "required": ["job_id"],
                                },
                            },
                        ]
                    },
                },
            )

        if path == "/mcp/tools/call":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "Mock execution successful",
                            }
                        ]
                    },
                },
            )

        return httpx.Response(
            404,
            json={
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "error": {"code": 404, "message": f"Unhandled path: {path}"},
            },
        )

    mock_transport = httpx.MockTransport(_mock_send)
    original_async_client = httpx.AsyncClient

    def _patched_async_client(*args, **kwargs):
        kwargs["transport"] = mock_transport
        return original_async_client(*args, **kwargs)

    from app.services.crewai.linkedin_recommended_jobs import crew as linkedin_module

    linkedin_module._MCP_FACTORY = None
    linkedin_module._MCP_TOOL_CACHE.clear()
    linkedin_module._cached_crew = None

    success = True

    class _StubAgent(dict):
        def __init__(self, *, config, tools, **kwargs):
            super().__init__()
            self.config = config
            self.tools = list(tools)
            self["config"] = config
            self["tools"] = self.tools

    class _StubTask(dict):
        def __init__(self, *, config, agent, context=None, **kwargs):
            super().__init__()
            self.config = config
            self.agent = agent
            self.context = context or []
            self.name = config.get("name") if isinstance(config, dict) else None
            self["config"] = config
            self["agent"] = agent
            self["context"] = self.context

    with patch("app.services.mcp.mcp_transport.httpx.AsyncClient", _patched_async_client), \
            patch("app.services.crewai.linkedin_recommended_jobs.crew.Agent", _StubAgent), \
            patch("app.services.crewai.linkedin_recommended_jobs.crew.Task", _StubTask):
        try:
            crew_instance = linkedin_module.LinkedInRecommendedJobsCrew()

            collector_tools = crew_instance.job_collector_agent().tools
            details_tools = crew_instance.job_details_agent().tools

            collector_names = {
                getattr(tool, "tool_name", getattr(tool, "name", "")) for tool in collector_tools
            }
            details_names = {
                getattr(tool, "tool_name", getattr(tool, "name", "")) for tool in details_tools
            }

            if "get_recommended_jobs" in collector_names:
                print("✅ Job collector agent received get_recommended_jobs tool")
            else:
                print("❌ Job collector agent missing get_recommended_jobs tool")
                success = False

            if "get_job_details" in details_names:
                print("✅ Job details agent received get_job_details tool")
            else:
                print("❌ Job details agent missing get_job_details tool")
                success = False

            if success:
                print("✅ Streaming transport successfully populated LinkedIn MCP tools")

        except Exception as exc:
            print(f"❌ Streaming transport MCP tool population failed: {exc}")
            success = False
        finally:
            factory = linkedin_module._MCP_FACTORY
            if factory is not None:
                try:
                    linkedin_module._run_coroutine_safely(factory.adapter.disconnect)
                except Exception as cleanup_error:
                    print(f"⚠️ MCP disconnect cleanup encountered an error: {cleanup_error}")
            linkedin_module._MCP_FACTORY = None
            linkedin_module._MCP_TOOL_CACHE.clear()
            linkedin_module._cached_crew = None

    for key, value in env_backup.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    return success


def main():
    """Run all MCP integration tests."""
    
    tests = [
        ("MCP Imports", test_mcp_imports),
        ("Crew Structure", test_crew_structure),
        ("Agent Tool Mapping", test_agent_tool_mapping),
        ("Service Integration", test_service_integration),
        ("API Endpoint", test_api_endpoint),
        ("Streaming Transport Tool Population", test_streaming_transport_tool_population),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 55}")
    print("MCP Integration Test Summary")
    print(f"{'=' * 55}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All MCP integration tests passed!")
        print("\nLinkedIn Recommended Jobs MCP Integration Summary:")
        print("✅ Properly imports from app.services.mcp")
        print("✅ Uses MCPConfig, MCPToolFactory, MCPToolWrapper from existing infrastructure")
        print("✅ Maps get_recommended_jobs and get_job_details MCP tools to agents")
        print("✅ Follows same MCP patterns as existing linkedin_job_search crew")
        print("✅ Service layer integrates with crew correctly")
        print("✅ API endpoint properly registered and integrated")
        print("\n🚀 Ready to use existing MCP functionality from phases 1-5!")
        return 0
    else:
        print(f"\n❌ {total - passed} MCP integration tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)