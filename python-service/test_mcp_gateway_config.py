#!/usr/bin/env python3
"""
Test script to validate MCP Gateway configuration.

This script checks if the MCP Gateway configuration is correct and can be loaded properly.
"""
import json
import sys
from pathlib import Path


def test_mcp_config():
    """Test MCP server configuration file."""
    print("🔍 Testing MCP Gateway Configuration")
    print("=" * 50)
    
    config_path = Path("mcp-config/servers.json")
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"✅ Config file loaded successfully")
        
        # Check required structure
        if "servers" not in config:
            print("❌ Missing 'servers' section in config")
            return False
            
        servers = config["servers"]
        print(f"📋 Found {len(servers)} server configurations:")
        
        for server_name, server_config in servers.items():
            print(f"  🔧 {server_name}:")
            
            # Check required fields
            required_fields = ["command", "args", "description"]
            missing_fields = []
            
            for field in required_fields:
                if field not in server_config:
                    missing_fields.append(field)
                else:
                    print(f"    ✅ {field}: {server_config[field]}")
            
            if missing_fields:
                print(f"    ❌ Missing required fields: {missing_fields}")
                return False
                
            # Check environment variables
            if "env" in server_config:
                env_vars = server_config["env"]
                print(f"    🌍 Environment variables: {len(env_vars)}")
                for key, value in env_vars.items():
                    print(f"      - {key}: {value}")
        
        # Check gateway configuration
        if "gateway" in config:
            gateway_config = config["gateway"]
            print(f"🌐 Gateway configuration:")
            print(f"  Port: {gateway_config.get('port', 'Not specified')}")
            print(f"  Host: {gateway_config.get('host', 'Not specified')}")
        
        print(f"\n✅ Configuration validation passed!")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        return False


def test_docker_compose_config():
    """Test docker-compose MCP Gateway configuration."""
    print(f"\n🔍 Testing Docker Compose MCP Gateway Configuration")
    print("-" * 50)
    
    compose_file = Path("../docker-compose.yml")
    if not compose_file.exists():
        print(f"❌ Docker compose file not found: {compose_file}")
        return False
    
    try:
        with open(compose_file, 'r') as f:
            content = f.read()
        
        # Check for mcp-gateway service
        if "mcp-gateway:" not in content:
            print("❌ mcp-gateway service not found in docker-compose.yml")
            return False
            
        print("✅ mcp-gateway service found")
        
        # Check key configuration elements
        checks = [
            ("--transport=stdio", "Stdio transport configured"),
            ("--port=8811", "Port 8811 configured"),
            ("--servers=", "Servers parameter configured"),
            ("docker/mcp-gateway", "Using correct image"),
            ("healthcheck:", "Health check configured"),
            ("/var/run/docker.sock", "Docker socket mounted"),
            ("./python-service/mcp-config:/config", "Config volume mounted")
        ]
        
        for check_text, description in checks:
            if check_text in content:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
                return False
        
        print(f"\n✅ Docker Compose configuration validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error reading docker-compose file: {e}")
        return False


def main():
    """Run all configuration tests."""
    print("🚀 MCP Gateway Configuration Validation")
    print("=" * 60)
    
    # Change to the directory containing the script
    script_dir = Path(__file__).parent
    original_cwd = Path.cwd()
    
    try:
        # Change to the script directory for relative paths
        import os
        os.chdir(script_dir)
        
        tests = [
            ("MCP Configuration", test_mcp_config),
            ("Docker Compose Configuration", test_docker_compose_config),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            print("=" * 40)
            
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print(f"\n{'=' * 60}")
        print("Configuration Validation Summary")
        print(f"{'=' * 60}")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "PASS" if result else "FAIL"
            emoji = "✅" if result else "❌"
            print(f"{emoji} {test_name}: {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All configuration tests passed!")
            print("\nMCP Gateway should be able to start successfully with this configuration.")
            return 0
        else:
            print(f"\n❌ {total - passed} configuration tests failed!")
            print("\nPlease fix the configuration issues before starting the gateway.")
            return 1
            
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)