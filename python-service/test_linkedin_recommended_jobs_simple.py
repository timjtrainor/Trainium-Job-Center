#!/usr/bin/env python3
"""
Simplified test for LinkedIn Recommended Jobs structure validation.

This script validates the crew files and configuration without requiring 
full CrewAI dependencies.
"""

import sys
import os
import yaml
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_file_structure():
    """Test that all required files exist."""
    print("📁 Testing File Structure...")
    
    base_path = Path("app/services/crewai/linkedin_recommended_jobs")
    required_files = [
        "__init__.py",
        "crew.py", 
        "README.md",
        "config/agents.yaml",
        "config/tasks.yaml"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = base_path / file_path
        if not full_path.exists():
            missing_files.append(str(full_path))
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present!")
    print(f"   Checked {len(required_files)} files")
    return True


def test_yaml_configuration():
    """Test that YAML files are valid and contain expected structure."""
    print("\n📋 Testing YAML Configuration...")
    
    base_path = Path("app/services/crewai/linkedin_recommended_jobs/config")
    
    try:
        # Test agents.yaml
        with open(base_path / "agents.yaml", "r") as f:
            agents_config = yaml.safe_load(f)
        
        expected_agents = ["job_collector_agent", "job_details_agent", "documentation_agent"]
        for agent in expected_agents:
            if agent not in agents_config:
                print(f"❌ Missing agent: {agent}")
                return False
            
            agent_config = agents_config[agent]
            required_fields = ["role", "goal", "backstory"]
            for field in required_fields:
                if field not in agent_config:
                    print(f"❌ Agent {agent} missing field: {field}")
                    return False
        
        # Test tasks.yaml
        with open(base_path / "tasks.yaml", "r") as f:
            tasks_config = yaml.safe_load(f)
        
        expected_tasks = ["collect_recommended_jobs_task", "fetch_job_details_task", "update_documentation_task"]
        for task in expected_tasks:
            if task not in tasks_config:
                print(f"❌ Missing task: {task}")
                return False
            
            task_config = tasks_config[task]
            required_fields = ["description", "expected_output", "agent"]
            for field in required_fields:
                if field not in task_config:
                    print(f"❌ Task {task} missing field: {field}")
                    return False
        
        print("✅ YAML configuration is valid!")
        print(f"   Agents: {len(agents_config)}")
        print(f"   Tasks: {len(tasks_config)}")
        return True
        
    except Exception as e:
        print(f"❌ YAML configuration error: {e}")
        return False


def test_agent_roles():
    """Test that agents have correct roles as specified in requirements."""
    print("\n👥 Testing Agent Roles...")
    
    base_path = Path("app/services/crewai/linkedin_recommended_jobs/config")
    
    try:
        with open(base_path / "agents.yaml", "r") as f:
            agents_config = yaml.safe_load(f)
        
        expected_roles = {
            "job_collector_agent": "LinkedIn Job Collector",
            "job_details_agent": "LinkedIn Job Details Fetcher", 
            "documentation_agent": "Project Documentation Maintainer"
        }
        
        for agent_key, expected_role in expected_roles.items():
            if agent_key not in agents_config:
                print(f"❌ Missing agent: {agent_key}")
                return False
            
            actual_role = agents_config[agent_key]["role"]
            if actual_role != expected_role:
                print(f"❌ Agent {agent_key} has wrong role: {actual_role} (expected: {expected_role})")
                return False
        
        print("✅ Agent roles are correct!")
        for agent_key, role in expected_roles.items():
            print(f"   {agent_key}: {role}")
        return True
        
    except Exception as e:
        print(f"❌ Agent role validation error: {e}")
        return False


def test_task_dependencies():
    """Test that tasks have correct dependencies."""
    print("\n🔗 Testing Task Dependencies...")
    
    base_path = Path("app/services/crewai/linkedin_recommended_jobs/config")
    
    try:
        with open(base_path / "tasks.yaml", "r") as f:
            tasks_config = yaml.safe_load(f)
        
        # Check dependencies
        expected_dependencies = {
            "collect_recommended_jobs_task": [],  # No dependencies
            "fetch_job_details_task": ["collect_recommended_jobs_task"],  # Depends on collect
            "update_documentation_task": ["collect_recommended_jobs_task", "fetch_job_details_task"]  # Depends on both
        }
        
        for task_key, expected_deps in expected_dependencies.items():
            task_config = tasks_config[task_key]
            actual_deps = task_config.get("context", [])
            
            if set(actual_deps) != set(expected_deps):
                print(f"❌ Task {task_key} has wrong dependencies: {actual_deps} (expected: {expected_deps})")
                return False
        
        print("✅ Task dependencies are correct!")
        print("   collect_recommended_jobs_task: no dependencies")
        print("   fetch_job_details_task: depends on collect task")
        print("   update_documentation_task: depends on both previous tasks")
        return True
        
    except Exception as e:
        print(f"❌ Task dependency validation error: {e}")
        return False


def test_mcp_tools_configuration():
    """Test that required MCP tools are referenced."""
    print("\n🔧 Testing MCP Tools Configuration...")
    
    crew_file = Path("app/services/crewai/linkedin_recommended_jobs/crew.py")
    
    try:
        with open(crew_file, "r") as f:
            crew_content = f.read()
        
        required_tools = ["get_recommended_jobs", "get_job_details"]
        
        for tool in required_tools:
            if tool not in crew_content:
                print(f"❌ MCP tool {tool} not found in crew.py")
                return False
        
        # Check that the tool mapping is correct
        if '"get_recommended_jobs"' not in crew_content:
            print("❌ get_recommended_jobs not properly configured")
            return False
            
        if '"get_job_details"' not in crew_content:
            print("❌ get_job_details not properly configured")
            return False
        
        print("✅ MCP tools configuration is correct!")
        print("   get_recommended_jobs: configured")
        print("   get_job_details: configured")
        return True
        
    except Exception as e:
        print(f"❌ MCP tools configuration error: {e}")
        return False


def test_jobposting_schema():
    """Test that JobPosting schema is correctly defined."""
    print("\n📊 Testing JobPosting Schema...")
    
    crew_file = Path("app/services/crewai/linkedin_recommended_jobs/crew.py")
    tasks_file = Path("app/services/crewai/linkedin_recommended_jobs/config/tasks.yaml")
    
    try:
        # Check schema keys in crew.py
        with open(crew_file, "r") as f:
            crew_content = f.read()
        
        required_schema_keys = ["title", "company", "location", "description", "url"]
        
        for key in required_schema_keys:
            if f'"{key}"' not in crew_content:
                print(f"❌ Schema key {key} not found in crew.py")
                return False
        
        # Check schema definition in tasks.yaml
        with open(tasks_file, "r") as f:
            tasks_content = f.read()
        
        for key in required_schema_keys:
            if key not in tasks_content:
                print(f"❌ Schema key {key} not documented in tasks.yaml")
                return False
        
        print("✅ JobPosting schema is correctly defined!")
        print(f"   Required fields: {', '.join(required_schema_keys)}")
        return True
        
    except Exception as e:
        print(f"❌ JobPosting schema validation error: {e}")
        return False


def test_readme_documentation():
    """Test that README contains required documentation."""
    print("\n📖 Testing README Documentation...")
    
    readme_file = Path("app/services/crewai/linkedin_recommended_jobs/README.md")
    
    try:
        with open(readme_file, "r") as f:
            readme_content = f.read()
        
        required_sections = [
            "Purpose",
            "Workflow", 
            "Agents",
            "Tasks",
            "Output Schema",
            "MCP Tools Required",
            "Usage",
            "Important Constraints"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in readme_content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing README sections: {missing_sections}")
            return False
        
        # Check that constraints are mentioned
        constraint_keywords = ["NOT include", "no recommendation", "no filtering", "no ranking"]
        constraint_found = any(keyword.lower() in readme_content.lower() for keyword in constraint_keywords)
        
        if not constraint_found:
            print("❌ Important constraints not clearly documented")
            return False
        
        print("✅ README documentation is complete!")
        print(f"   Contains all {len(required_sections)} required sections")
        print("   Clearly states constraints about no recommendation logic")
        return True
        
    except Exception as e:
        print(f"❌ README documentation error: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🚀 LinkedIn Recommended Jobs Crew Validation")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("YAML Configuration", test_yaml_configuration), 
        ("Agent Roles", test_agent_roles),
        ("Task Dependencies", test_task_dependencies),
        ("MCP Tools Configuration", test_mcp_tools_configuration),
        ("JobPosting Schema", test_jobposting_schema),
        ("README Documentation", test_readme_documentation),
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
    print("Validation Summary")
    print(f"{'=' * 50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n🎉 All validations passed!")
        print("\nLinkedIn Recommended Jobs Crew Summary:")
        print("✅ File structure follows CrewAI patterns")
        print("✅ YAML configuration is valid and complete")
        print("✅ Agent roles match requirements exactly")
        print("✅ Task dependencies configured for sequential execution")
        print("✅ MCP tools (get_recommended_jobs, get_job_details) integrated")
        print("✅ JobPosting schema (title, company, location, description, url) defined")
        print("✅ Documentation complete with clear constraints")
        print("\nThe crew implementation is structurally correct and ready!")
        return 0
    else:
        print(f"\n❌ {total - passed} validations failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)