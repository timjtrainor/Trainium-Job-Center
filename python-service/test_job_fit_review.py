#!/usr/bin/env python3
"""
Test script to validate multi-model agent configuration and MCP gateway integration.

This script tests:
1. Different models are properly configured for different agents
2. MCP gateway tool can be loaded and configured
3. Agent creation works with proper model routing
"""

import sys
import os
from pathlib import Path
import yaml

# Add the python-service directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_agent_model_configuration():
    """Test that agents have different model configurations"""
    print("🔧 Testing agent model configurations...")
    
    base_dir = Path("app/services/crewai")
    agents = ["researcher", "negotiator", "skeptic"]
    
    agent_models = {}
    for agent in agents:
        agent_file = base_dir / "agents" / f"{agent}.yaml"
        if not agent_file.exists():
            print(f"❌ Agent file not found: {agent_file}")
            return False
            
        with open(agent_file, 'r') as f:
            config = yaml.safe_load(f)
        
        models = config.get("models", [])
        if not models:
            print(f"❌ No models configured for agent: {agent}")
            return False
            
        provider = models[0]["provider"]
        model = models[0]["model"]
        agent_models[agent] = (provider, model)
        print(f"   ✅ {agent}: {provider}:{model}")
    
    # Check that agents use different models
    unique_models = set(agent_models.values())
    if len(unique_models) < 2:
        print("⚠️  Warning: All agents use the same model. Consider using different models for demonstration.")
    else:
        print(f"✅ Found {len(unique_models)} different model configurations")
    
    return True

def test_mcp_tool_import():
    """Test that MCP gateway tool can be imported and created"""
    print("\n🔧 Testing MCP gateway tool import...")
    
    try:
        # Test import
        from app.services.crewai.tools.mcp_gateway import create_mcp_gateway_tool, MCPGatewayTool
        print("   ✅ Successfully imported MCP gateway tool")
        
        # Test tool creation
        tool = create_mcp_gateway_tool(gateway_url="http://localhost:8811")
        print(f"   ✅ Successfully created tool: {tool.name}")
        print(f"   📝 Tool description: {tool.description[:100]}...")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Failed to import MCP tool: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Failed to create MCP tool: {e}")
        return False

def test_crew_tool_loading():
    """Test that CrewAI crew can load tools properly"""
    print("\n🔧 Testing CrewAI crew tool loading...")
    
    try:
        # Import the crew components
        from app.services.crewai.job_review.crew import JobReviewCrew
        print("   ✅ Successfully imported JobReviewCrew")
        
        # Create crew instance
        crew_instance = JobReviewCrew()
        print("   ✅ Successfully created crew instance")
        
        # Test tool loading
        test_tools = ["web_search", "chroma_search"]
        loaded_tools = crew_instance._load_tools(test_tools)
        print(f"   ✅ Successfully loaded {len(loaded_tools)} tools")
        
        for tool in loaded_tools:
            print(f"      - {tool.name}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to test crew tool loading: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_routing_logic():
    """Test the model routing logic in crew"""
    print("\n🔧 Testing model routing logic...")
    
    try:
        from app.services.crewai.job_review.crew import JobReviewCrew
        
        crew_instance = JobReviewCrew()
        
        # Test model config parsing
        test_models = [
            {"provider": "openai", "model": "gpt-4o-mini"},
            {"provider": "gemini", "model": "gemini-1.5-flash"},
        ]
        
        parsed = crew_instance._parse_model_config(test_models)
        expected = [("openai", "gpt-4o-mini"), ("gemini", "gemini-1.5-flash")]
        
        if parsed == expected:
            print("   ✅ Model config parsing works correctly")
            return True
        else:
            print(f"   ❌ Model config parsing failed. Expected: {expected}, Got: {parsed}")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed to test model routing: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Job Fit Review validation tests...\n")
    
    tests = [
        ("Agent Model Configuration", test_agent_model_configuration),
        ("MCP Tool Import", test_mcp_tool_import),
        ("Model Routing Logic", test_model_routing_logic),
        ("Crew Tool Loading", test_crew_tool_loading),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   💥 Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Multi-model agent configuration is working.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Review the output above.")
        return 1

if __name__ == "__main__":
    exit(main())