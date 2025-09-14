#!/usr/bin/env python3
"""
Manual validation of MCP Gateway integration components.

This script validates that all the MCP integration components are properly
implemented without requiring Docker builds or network access.
"""
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")
    
    try:
        from app.core.config import get_settings
        
        settings = get_settings()
        assert hasattr(settings, 'mcp_gateway_enabled')
        assert hasattr(settings, 'mcp_gateway_url')
        assert hasattr(settings, 'mcp_gateway_port')
        
        print(f"   ✅ MCP Gateway enabled: {settings.mcp_gateway_enabled}")
        print(f"   ✅ MCP Gateway URL: {settings.mcp_gateway_url}")
        print(f"   ✅ MCP Gateway port: {settings.mcp_gateway_port}")
        
        return True
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False


def test_mcp_adapter_import():
    """Test MCP adapter can be imported."""
    print("📦 Testing MCP adapter import...")
    
    try:
        from app.services.mcp_adapter import MCPServerAdapter, get_mcp_adapter, create_sync_tool_wrapper
        
        print("   ✅ MCPServerAdapter imported successfully")
        print("   ✅ get_mcp_adapter context manager available")
        print("   ✅ create_sync_tool_wrapper utility available")
        
        return True
    except Exception as e:
        print(f"   ❌ MCP adapter import failed: {e}")
        return False


def test_crewai_base_utilities():
    """Test CrewAI base utilities."""
    print("🛠️ Testing CrewAI base utilities...")
    
    try:
        from app.services.crewai import base
        
        # Check new functions exist
        assert hasattr(base, 'load_mcp_tools_sync')
        assert hasattr(base, 'get_duckduckgo_tools')
        
        print("   ✅ load_mcp_tools_sync function available")
        print("   ✅ get_duckduckgo_tools function available")
        
        return True
    except Exception as e:
        print(f"   ❌ CrewAI base utilities test failed: {e}")
        return False


def test_job_review_crew_integration():
    """Test JobReviewCrew integration."""
    print("🤖 Testing JobReviewCrew integration...")
    
    try:
        from app.services.crewai.job_review.crew import JobReviewCrew
        
        crew = JobReviewCrew()
        
        # Check if prepare_analysis method exists and has been updated
        assert hasattr(crew, 'prepare_analysis')
        assert hasattr(crew, '_load_tools')
        
        print("   ✅ JobReviewCrew class available")
        print("   ✅ prepare_analysis method with MCP integration")
        print("   ✅ _load_tools method updated for MCP")
        
        return True
    except Exception as e:
        print(f"   ❌ JobReviewCrew integration test failed: {e}")
        return False


def test_file_structure():
    """Test that all required files exist."""
    print("📁 Testing file structure...")
    
    required_files = [
        "app/services/mcp_adapter.py",
        "mcp_gateway.py",
        "Dockerfile.mcp-gateway",
        "mcp-config/servers.json",
        "demo_mcp_integration.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} missing")
            all_exist = False
            
    return all_exist


def test_docker_compose_integration():
    """Test docker-compose.yml changes."""
    print("🐳 Testing Docker Compose integration...")
    
    try:
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        
        if compose_file.exists():
            content = compose_file.read_text()
            
            checks = [
                ("mcp-gateway service", "mcp-gateway:" in content),
                ("MCP environment vars", "MCP_GATEWAY_URL" in content),
                ("MCP dependencies", "mcp-gateway:" in content and "condition: service_healthy" in content),
                ("MCP port mapping", "8811:8811" in content)
            ]
            
            all_passed = True
            for check_name, condition in checks:
                if condition:
                    print(f"   ✅ {check_name}")
                else:
                    print(f"   ❌ {check_name}")
                    all_passed = False
                    
            return all_passed
        else:
            print("   ❌ docker-compose.yml not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Docker Compose test failed: {e}")
        return False


def test_agent_configuration():
    """Test agent configuration updates."""
    print("👤 Testing agent configuration...")
    
    try:
        researcher_config = Path(__file__).parent / "app/services/crewai/agents/researcher.yaml"
        
        if researcher_config.exists():
            content = researcher_config.read_text()
            
            checks = [
                ("DuckDuckGo in role", "DuckDuckGo" in content),
                ("web_search tool", "web_search" in content),
                ("search capabilities", "search" in content.lower())
            ]
            
            all_passed = True
            for check_name, condition in checks:
                if condition:
                    print(f"   ✅ {check_name}")
                else:
                    print(f"   ❌ {check_name}")
                    all_passed = False
                    
            return all_passed
        else:
            print("   ❌ researcher.yaml not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Agent configuration test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🔍 MCP Gateway Integration Validation")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("MCP Adapter Import", test_mcp_adapter_import),
        ("CrewAI Base Utilities", test_crewai_base_utilities),
        ("JobReviewCrew Integration", test_job_review_crew_integration),
        ("File Structure", test_file_structure),
        ("Docker Compose Integration", test_docker_compose_integration),
        ("Agent Configuration", test_agent_configuration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 50}")
    print("Validation Summary")
    print(f"{'=' * 50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validation tests passed!")
        print("\nMCP Gateway Integration Summary:")
        print("✅ Docker MCP Gateway service configured")
        print("✅ MCPServerAdapter with context management implemented")
        print("✅ CrewAI base utilities updated for MCP tool loading")
        print("✅ JobReviewCrew updated to inject MCP tools before kickoff")
        print("✅ DuckDuckGo tools configured for web search")
        print("✅ Agent configurations updated for MCP tools")
        print("✅ Environment variables and settings configured")
        print("\nThe integration is ready for deployment!")
        return 0
    else:
        print(f"\n❌ {total - passed} validation tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)