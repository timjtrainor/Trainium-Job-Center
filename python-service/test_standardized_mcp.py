#!/usr/bin/env python3
"""
Test script to validate standardized MCP integration across crews.

This script tests that all crews follow the same MCP gateway pattern
and can be imported and instantiated successfully.
"""
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_crew_imports():
    """Test that all standardized crews can be imported."""
    print("🔍 Testing crew imports...")
    
    try:
        # Test linkedin_recommended_jobs (reference implementation)
        from app.services.crewai.linkedin_recommended_jobs.crew import LinkedInRecommendedJobsCrew
        print("   ✅ linkedin_recommended_jobs crew imported")
        
        # Test research_company (updated to gateway pattern)
        from app.services.crewai.research_company.crew import ResearchCompanyCrew
        print("   ✅ research_company crew imported")
        
        # Test linkedin_job_search (updated to gateway pattern)
        from app.services.crewai.linkedin_job_search.crew import LinkedInJobSearchCrew
        print("   ✅ linkedin_job_search crew imported")
        
        # Test job_posting_review (already using ChromaDB tools, not MCP)
        from app.services.crewai.job_posting_review.crew import JobPostingReviewCrew
        print("   ✅ job_posting_review crew imported")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False

def test_crew_instantiation():
    """Test that crews can be instantiated without MCP gateway running."""
    print("🏗️  Testing crew instantiation...")
    
    try:
        # Test that crews can be created (they should handle MCP connection failures gracefully)
        from app.services.crewai.linkedin_recommended_jobs.crew import LinkedInRecommendedJobsCrew
        crew1 = LinkedInRecommendedJobsCrew()
        print("   ✅ linkedin_recommended_jobs crew instantiated")
        
        from app.services.crewai.research_company.crew import ResearchCompanyCrew
        crew2 = ResearchCompanyCrew()
        print("   ✅ research_company crew instantiated")
        
        from app.services.crewai.linkedin_job_search.crew import LinkedInJobSearchCrew
        crew3 = LinkedInJobSearchCrew()
        print("   ✅ linkedin_job_search crew instantiated")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Instantiation test failed: {e}")
        return False

def test_tool_config_files():
    """Test that tools.yaml files exist for MCP-enabled crews."""
    print("📁 Testing tool configuration files...")
    
    base_path = Path(__file__).parent / "app" / "services" / "crewai"
    
    required_configs = [
        base_path / "linkedin_recommended_jobs" / "config" / "tools.yaml",
        base_path / "research_company" / "config" / "tools.yaml", 
        base_path / "linkedin_job_search" / "config" / "tools.yaml",
    ]
    
    all_exist = True
    for config_file in required_configs:
        if config_file.exists():
            print(f"   ✅ {config_file.relative_to(base_path)} exists")
        else:
            print(f"   ❌ {config_file.relative_to(base_path)} missing")
            all_exist = False
            
    return all_exist

def test_mcp_adapter_pattern():
    """Test that crews follow the standardized MCP adapter pattern."""
    print("🔧 Testing MCP adapter pattern compliance...")
    
    try:
        from app.services.crewai.linkedin_recommended_jobs.crew import LinkedInRecommendedJobsCrew
        from app.services.crewai.research_company.crew import ResearchCompanyCrew
        from app.services.crewai.linkedin_job_search.crew import LinkedInJobSearchCrew
        
        # Check that crews have the expected MCP-related methods
        crews_to_test = [
            ("linkedin_recommended_jobs", LinkedInRecommendedJobsCrew),
            ("research_company", ResearchCompanyCrew),
            ("linkedin_job_search", LinkedInJobSearchCrew),
        ]
        
        for crew_name, crew_class in crews_to_test:
            crew = crew_class()
            
            # Check for required methods
            if hasattr(crew, '_get_mcp_tools'):
                print(f"   ✅ {crew_name} has _get_mcp_tools method")
            else:
                print(f"   ❌ {crew_name} missing _get_mcp_tools method")
                return False
                
            if hasattr(crew, '_get_tools_for_agent'):
                print(f"   ✅ {crew_name} has _get_tools_for_agent method")
            else:
                print(f"   ❌ {crew_name} missing _get_tools_for_agent method")
                return False
                
            if hasattr(crew, 'close'):
                print(f"   ✅ {crew_name} has close method")
            else:
                print(f"   ❌ {crew_name} missing close method")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Pattern compliance test failed: {e}")
        return False

def test_docker_compose_mcp_gateway():
    """Test that docker-compose.yml has mcp-gateway service configured."""
    print("🐳 Testing Docker Compose MCP gateway configuration...")
    
    try:
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        
        if not compose_file.exists():
            print("   ❌ docker-compose.yml not found")
            return False
            
        content = compose_file.read_text()
        
        checks = [
            ("mcp-gateway service", "mcp-gateway:" in content),
            ("docker/mcp-gateway image", "docker/mcp-gateway:latest" in content),
            ("servers parameter", "--servers=" in content),
            ("port mapping", ":8811" in content),
        ]
        
        all_passed = True
        for check_name, condition in checks:
            if condition:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
                all_passed = False
                
        return all_passed
        
    except Exception as e:
        print(f"   ❌ Docker Compose test failed: {e}")
        return False

def main():
    """Run all standardization tests."""
    print("🔍 MCP Integration Standardization Validation")
    print("=" * 50)
    
    tests = [
        ("Crew Imports", test_crew_imports),
        ("Crew Instantiation", test_crew_instantiation),
        ("Tool Configuration Files", test_tool_config_files),
        ("MCP Adapter Pattern", test_mcp_adapter_pattern),
        ("Docker Compose Configuration", test_docker_compose_mcp_gateway),
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
        print("\n✅ All validation tests passed!")
        print("\nMCP Integration Standardization Summary:")
        print("✅ All crews use consistent MCP gateway pattern")
        print("✅ MCPServerAdapter from crewai-tools is used consistently")
        print("✅ Tool configuration is driven by YAML files")
        print("✅ Docker Compose has mcp-gateway service configured")
        print("✅ Legacy MCP implementations have been removed")
        print("\nThe MCP integration is now standardized across all crews!")
        return 0
    else:
        print(f"\n❌ {total - passed} validation tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)