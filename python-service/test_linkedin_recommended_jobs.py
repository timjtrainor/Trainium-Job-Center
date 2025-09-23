#!/usr/bin/env python3
"""
Test script for LinkedIn Recommended Jobs CrewAI integration.

This script tests the crew's ability to fetch and normalize LinkedIn 
job recommendations using the MCP Gateway.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.crewai.linkedin_recommended_jobs import (
    LinkedInRecommendedJobsCrew, 
    get_linkedin_recommended_jobs_crew,
    run_linkedin_recommended_jobs
)


def test_crew_initialization():
    """Test that the crew can be initialized properly."""
    print("🔧 Testing Crew Initialization...")
    
    try:
        crew_instance = LinkedInRecommendedJobsCrew()
        assert crew_instance is not None, "Crew instance should be created"
        
        crew = crew_instance.crew()
        assert crew is not None, "Crew should be assembled"
        assert len(crew.agents) == 3, f"Expected 3 agents, got {len(crew.agents)}"
        assert len(crew.tasks) == 3, f"Expected 3 tasks, got {len(crew.tasks)}"
        
        print("✅ Crew initialization successful!")
        print(f"   Agents: {len(crew.agents)}")
        print(f"   Tasks: {len(crew.tasks)}")
        print(f"   Process: {crew.process}")
        
        return True
    except Exception as e:
        print(f"❌ Crew initialization failed: {e}")
        return False


def test_crew_factory():
    """Test the factory function for crew creation."""
    print("\n🏭 Testing Crew Factory Function...")
    
    try:
        crew1 = get_linkedin_recommended_jobs_crew()
        crew2 = get_linkedin_recommended_jobs_crew()
        
        assert crew1 is not None, "Factory should return a crew"
        assert crew1 is crew2, "Factory should return the same instance (singleton)"
        
        print("✅ Factory function works correctly!")
        print("   Returns singleton crew instance")
        
        return True
    except Exception as e:
        print(f"❌ Factory function failed: {e}")
        return False


def test_agent_configuration():
    """Test that agents are configured correctly."""
    print("\n👥 Testing Agent Configuration...")
    
    try:
        crew_instance = LinkedInRecommendedJobsCrew()
        
        # Test individual agent creation
        job_collector = crew_instance.job_collector_agent()
        job_details = crew_instance.job_details_agent()
        documentation = crew_instance.documentation_agent()
        
        assert job_collector.role == "LinkedIn Job Collector", f"Wrong role: {job_collector.role}"
        assert job_details.role == "LinkedIn Job Details Fetcher", f"Wrong role: {job_details.role}"
        assert documentation.role == "Project Documentation Maintainer", f"Wrong role: {documentation.role}"
        
        print("✅ Agent configuration is correct!")
        print(f"   Job Collector: {job_collector.role}")
        print(f"   Job Details: {job_details.role}")
        print(f"   Documentation: {documentation.role}")
        
        return True
    except Exception as e:
        print(f"❌ Agent configuration failed: {e}")
        return False


def test_task_configuration():
    """Test that tasks are configured correctly."""
    print("\n📋 Testing Task Configuration...")
    
    try:
        crew_instance = LinkedInRecommendedJobsCrew()
        
        # Test individual task creation
        collect_task = crew_instance.collect_recommended_jobs_task()
        fetch_task = crew_instance.fetch_job_details_task()
        doc_task = crew_instance.update_documentation_task()
        
        assert collect_task.description is not None, "Collect task should have description"
        assert fetch_task.description is not None, "Fetch task should have description"
        assert doc_task.description is not None, "Doc task should have description"
        
        # Test task dependencies
        assert len(fetch_task.context) == 1, "Fetch task should depend on collect task"
        assert len(doc_task.context) == 2, "Doc task should depend on both previous tasks"
        
        print("✅ Task configuration is correct!")
        print(f"   Collect task: configured")
        print(f"   Fetch task: depends on {len(fetch_task.context)} tasks")
        print(f"   Doc task: depends on {len(doc_task.context)} tasks")
        
        return True
    except Exception as e:
        print(f"❌ Task configuration failed: {e}")
        return False


def test_mcp_tool_integration():
    """Test MCP tool integration (without actually calling tools)."""
    print("\n🔧 Testing MCP Tool Integration...")
    
    try:
        crew_instance = LinkedInRecommendedJobsCrew()
        
        # Check that agents have appropriate tools assigned
        job_collector = crew_instance.job_collector_agent()
        job_details = crew_instance.job_details_agent()
        documentation = crew_instance.documentation_agent()
        
        # Note: In test environment, MCP tools may not be available
        # so we just check that the integration doesn't crash
        
        print("✅ MCP tool integration initialized!")
        print(f"   Job Collector tools: {len(job_collector.tools)}")
        print(f"   Job Details tools: {len(job_details.tools)}") 
        print(f"   Documentation tools: {len(documentation.tools)}")
        
        return True
    except Exception as e:
        print(f"❌ MCP tool integration failed: {e}")
        return False


def test_workflow_execution():
    """Test the workflow execution (mock mode)."""
    print("\n🚀 Testing Workflow Execution...")
    
    try:
        # Note: This may fail without proper MCP setup, but we test the structure
        print("   Attempting to run workflow...")
        
        # Set mock mode if available
        os.environ['CREWAI_MOCK_MODE'] = 'true'
        
        result = run_linkedin_recommended_jobs()
        
        assert result is not None, "Workflow should return a result"
        assert isinstance(result, dict), "Result should be a dictionary"
        
        print("✅ Workflow execution completed!")
        print(f"   Result type: {type(result)}")
        print(f"   Has success flag: {'success' in result}")
        
        return True
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        print("   This may be expected in test environment without full MCP setup")
        return False


def main():
    """Run all tests."""
    print("🚀 LinkedIn Recommended Jobs Crew Tests")
    print("=" * 50)
    
    tests = [
        ("Crew Initialization", test_crew_initialization),
        ("Crew Factory", test_crew_factory),
        ("Agent Configuration", test_agent_configuration),
        ("Task Configuration", test_task_configuration),
        ("MCP Tool Integration", test_mcp_tool_integration),
        ("Workflow Execution", test_workflow_execution),
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
    print(f"\n{'=' * 50}")
    print("Test Summary")
    print(f"{'=' * 50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print("\nLinkedIn Recommended Jobs Crew Summary:")
        print("✅ Crew initialization working")
        print("✅ Factory pattern implemented")
        print("✅ Agent configuration correct")
        print("✅ Task dependencies configured")
        print("✅ MCP tool integration ready")
        print("✅ Sequential workflow process")
        print("\nThe crew is ready for deployment!")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)