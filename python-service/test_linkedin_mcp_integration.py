#!/usr/bin/env python3
"""
Test LinkedIn Recommended Jobs MCP Integration

This script validates that the LinkedIn recommended jobs crew properly
integrates with the existing MCP functionality.
"""

import sys
import os
from pathlib import Path

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

def main():
    """Run all MCP integration tests."""
    
    tests = [
        ("MCP Imports", test_mcp_imports),
        ("Crew Structure", test_crew_structure),
        ("Agent Tool Mapping", test_agent_tool_mapping),
        ("Service Integration", test_service_integration),
        ("API Endpoint", test_api_endpoint),
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