#!/usr/bin/env python3
"""
Simple validation script for multi-model agent configuration.

This script validates the YAML configuration without requiring heavy dependencies.
"""

import yaml
from pathlib import Path

def validate_agent_configurations():
    """Validate that agents have different model configurations"""
    print("🔧 Validating agent model configurations...")
    
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
        
        # Validate required fields
        required_fields = ["id", "role", "goal", "backstory", "models"]
        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            print(f"❌ Agent {agent} missing fields: {missing_fields}")
            return False
        
        models = config.get("models", [])
        if not models:
            print(f"❌ No models configured for agent: {agent}")
            return False
            
        provider = models[0]["provider"]
        model = models[0]["model"]
        agent_models[agent] = (provider, model)
        
        # Validate tools
        tools = config.get("tools", [])
        print(f"   ✅ {agent}: {provider}:{model} (tools: {tools})")
    
    # Check that agents use different models
    unique_models = set(agent_models.values())
    print(f"\n📊 Summary:")
    print(f"   - Total agents: {len(agents)}")
    print(f"   - Unique model configurations: {len(unique_models)}")
    
    if len(unique_models) >= 2:
        print("   ✅ Agents use different models - per-agent model selection enabled")
    else:
        print("   ⚠️  All agents use the same model")
    
    return True

def validate_mcp_gateway_structure():
    """Validate MCP gateway directory structure"""
    print("\n🔧 Validating MCP gateway structure...")
    
    gateway_dir = Path("../docker/mcp-gateway")
    required_files = [
        "main.py",
        "Dockerfile", 
        "requirements.txt",
        "config/servers.yaml"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = gateway_dir / file_path
        if not full_path.exists():
            missing_files.append(str(full_path))
        else:
            print(f"   ✅ Found: {file_path}")
    
    if missing_files:
        print(f"   ❌ Missing files: {missing_files}")
        return False
    
    return True

def validate_docker_compose():
    """Validate docker-compose includes MCP gateway service"""
    print("\n🔧 Validating docker-compose configuration...")
    
    compose_file = Path("../docker-compose.yml")
    if not compose_file.exists():
        print(f"   ❌ docker-compose.yml not found")
        return False
    
    with open(compose_file, 'r') as f:
        content = f.read()
    
    if "mcp-gateway:" in content:
        print("   ✅ MCP gateway service found in docker-compose.yml")
        
        # Check for key components
        checks = [
            ("ports:", "Port mapping"),
            ("healthcheck:", "Health check"),
            ("build:", "Build configuration"),
        ]
        
        for check, description in checks:
            if check in content:
                print(f"   ✅ {description} configured")
            else:
                print(f"   ⚠️  {description} may be missing")
        
        return True
    else:
        print("   ❌ MCP gateway service not found in docker-compose.yml")
        return False

def validate_crewai_tool():
    """Validate MCP gateway tool structure"""
    print("\n🔧 Validating CrewAI MCP tool...")
    
    tool_file = Path("app/services/crewai/tools/mcp_gateway.py")
    if not tool_file.exists():
        print(f"   ❌ MCP gateway tool not found: {tool_file}")
        return False
    
    with open(tool_file, 'r') as f:
        content = f.read()
    
    # Check for key components
    checks = [
        ("class MCPGatewayTool", "Tool class definition"),
        ("def _execute", "Execute method"),
        ("def create_mcp_gateway_tool", "Factory function"),
        ("args_schema", "Input schema"),
    ]
    
    for check, description in checks:
        if check in content:
            print(f"   ✅ {description} found")
        else:
            print(f"   ❌ {description} missing")
            return False
    
    return True

def main():
    """Run all validations"""
    print("🚀 Validating Job Fit Review implementation...\n")
    
    validations = [
        ("Agent Model Configuration", validate_agent_configurations),
        ("MCP Gateway Structure", validate_mcp_gateway_structure),
        ("Docker Compose Configuration", validate_docker_compose),
        ("CrewAI MCP Tool", validate_crewai_tool),
    ]
    
    results = []
    for validation_name, validation_func in validations:
        try:
            result = validation_func()
            results.append((validation_name, result))
        except Exception as e:
            print(f"   💥 Validation '{validation_name}' failed: {e}")
            results.append((validation_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    
    passed = 0
    for validation_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {validation_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} validations passed")
    
    if passed == len(results):
        print("\n🎉 All validations passed! Implementation looks good.")
        print("\n📋 Next steps:")
        print("   1. Build and start services: docker-compose up --build")
        print("   2. Test MCP gateway: curl http://localhost:8811/health")
        print("   3. Run job review crew with different models")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} validation(s) failed.")
        return 1

if __name__ == "__main__":
    exit(main())