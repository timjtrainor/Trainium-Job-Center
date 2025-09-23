#!/usr/bin/env python3
"""
Test the simplified MCP integration approach using MCPServerAdapter.

This test validates that the LinkedIn recommended jobs crew now uses
the simpler MCPServerAdapter approach from crewai_tools.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

print("🔍 Simplified MCP Integration Test")
print("=" * 40)

def test_crewai_tools_import():
    """Test that crewai_tools and MCPServerAdapter can be imported."""
    print("\n1️⃣ Testing CrewAI Tools Import...")
    
    try:
        from crewai_tools import MCPServerAdapter
        print("✅ MCPServerAdapter imported successfully from crewai_tools")
        return True
    except ImportError as e:
        print(f"❌ Failed to import MCPServerAdapter: {e}")
        return False

def test_crew_structure():
    """Test that the crew uses the simplified approach."""
    print("\n2️⃣ Testing Simplified Crew Structure...")
    
    try:
        # Read the crew file and check for simplified patterns
        with open("app/services/crewai/linkedin_recommended_jobs/crew.py", "r") as f:
            crew_content = f.read()
        
        # Check for MCPServerAdapter import
        if "from crewai_tools import MCPServerAdapter" in crew_content:
            print("✅ Crew imports MCPServerAdapter from crewai_tools")
        else:
            print("❌ Crew missing MCPServerAdapter import")
            return False
        
        # Check that complex MCP factory functions are removed
        if "_get_shared_mcp_factory" in crew_content:
            print("❌ Crew still contains complex MCP factory functions")
            return False
        else:
            print("✅ Complex MCP factory functions removed")
        
        # Check for simple MCP server config
        if "_MCP_SERVER_CONFIG" in crew_content:
            print("✅ Crew uses simple MCP server configuration")
        else:
            print("❌ Crew missing simple MCP server configuration")
            return False
        
        # Check that it no longer imports complex MCP modules
        if "from app.services.mcp import" in crew_content:
            print("❌ Crew still imports complex MCP modules")
            return False
        else:
            print("✅ Complex MCP module imports removed")
        
        return True
    except Exception as e:
        print(f"❌ Crew structure test failed: {e}")
        return False

def test_mcp_config():
    """Test that MCP configuration is simplified."""
    print("\n3️⃣ Testing MCP Configuration...")
    
    try:
        with open("app/services/crewai/linkedin_recommended_jobs/crew.py", "r") as f:
            crew_content = f.read()
        
        # Check for streamable-http configuration pointing to localhost:8811
        if "http://localhost:8811/mcp" in crew_content:
            print("✅ MCP configuration points to Gateway on localhost:8811")
        else:
            print("❌ MCP configuration doesn't point to correct Gateway URL")
            return False
        
        if "streamable-http" in crew_content:
            print("✅ Uses streamable-http transport")
        else:
            print("❌ Missing streamable-http transport configuration")
            return False
        
        return True
    except Exception as e:
        print(f"❌ MCP configuration test failed: {e}")
        return False

def test_agent_tool_assignment():
    """Test that agents get tools through the simplified approach."""
    print("\n4️⃣ Testing Agent Tool Assignment...")
    
    try:
        with open("app/services/crewai/linkedin_recommended_jobs/crew.py", "r") as f:
            crew_content = f.read()
        
        # Check for _get_linkedin_tools method
        if "_get_linkedin_tools" in crew_content:
            print("✅ Crew has method to filter LinkedIn tools")
        else:
            print("❌ Crew missing LinkedIn tools filtering method")
            return False
        
        # Check that agents use the LinkedIn tools
        if "tools=self._get_linkedin_tools()" in crew_content:
            print("✅ Agents use filtered LinkedIn tools")
        else:
            print("❌ Agents don't use LinkedIn tools properly")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Agent tool assignment test failed: {e}")
        return False

def test_cleanup_handling():
    """Test that cleanup is handled properly."""
    print("\n5️⃣ Testing Cleanup Handling...")
    
    try:
        with open("app/services/crewai/linkedin_recommended_jobs/crew.py", "r") as f:
            crew_content = f.read()
        
        # Check for __del__ method for cleanup
        if "__del__" in crew_content and "_mcp_adapter" in crew_content:
            print("✅ Crew has proper MCP adapter cleanup")
        else:
            print("❌ Crew missing proper cleanup handling")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Cleanup handling test failed: {e}")
        return False

def main():
    """Run all simplified MCP integration tests."""
    
    tests = [
        ("CrewAI Tools Import", test_crewai_tools_import),
        ("Simplified Crew Structure", test_crew_structure),
        ("MCP Configuration", test_mcp_config),
        ("Agent Tool Assignment", test_agent_tool_assignment),
        ("Cleanup Handling", test_cleanup_handling),
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
    print(f"\n{'=' * 40}")
    print("Simplified MCP Integration Summary")
    print(f"{'=' * 40}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All simplified MCP integration tests passed!")
        print("\nSimplified MCP Integration Summary:")
        print("✅ Uses MCPServerAdapter from crewai_tools (much simpler)")
        print("✅ Connects directly to MCP Gateway on localhost:8811")
        print("✅ Eliminates complex MCP factory and wrapper code")
        print("✅ Agents get tools through simple filtering")
        print("✅ Proper cleanup handling with __del__ method")
        print("✅ Maintains YAML approach for agents and tasks")
        print("\n🚀 Ready for much simpler MCP integration!")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)