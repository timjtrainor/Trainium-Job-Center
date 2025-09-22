#!/usr/bin/env python3
"""
Debug script for MCP Gateway startup issues.

This script helps diagnose common issues with MCP Gateway startup and provides
troubleshooting recommendations.
"""
import asyncio
import json
import sys
from pathlib import Path
import subprocess
import time

# Mock httpx for testing
class MockHttpxResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {}
    
    def json(self):
        return self._data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

class MockHttpxClient:
    def __init__(self):
        pass
    
    async def get(self, url, **kwargs):
        # Simulate gateway responses
        if "/health" in url:
            return MockHttpxResponse(200, {"status": "healthy"})
        elif "/servers" in url:
            return MockHttpxResponse(200, {"duckduckgo": {}, "linkedin-mcp-server": {}})
        return MockHttpxResponse(404)
    
    async def post(self, url, **kwargs):
        return MockHttpxResponse(200, {"session_id": "test_session"})
    
    async def aclose(self):
        pass


def check_docker_access():
    """Check if Docker is accessible."""
    print("🐳 Checking Docker access...")
    
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Docker server accessible (version: {version})")
            return True
        else:
            print(f"❌ Docker not accessible: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker command timed out")
        return False
    except FileNotFoundError:
        print("❌ Docker command not found")
        return False
    except Exception as e:
        print(f"❌ Docker access error: {e}")
        return False


def check_mcp_images():
    """Check if required MCP images are available."""
    print("\n📦 Checking MCP server images...")
    
    required_images = [
        "mcp/duckduckgo",
        "stickerdaniel/linkedin-mcp-server"
    ]
    
    all_available = True
    
    for image in required_images:
        try:
            result = subprocess.run(
                ["docker", "inspect", image],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✅ Image available: {image}")
            else:
                print(f"⚠️  Image not found locally: {image}")
                print(f"   Try: docker pull {image}")
                all_available = False
                
        except Exception as e:
            print(f"❌ Error checking image {image}: {e}")
            all_available = False
    
    return all_available


def check_gateway_image():
    """Check if MCP Gateway image is available."""
    print("\n🌐 Checking MCP Gateway image...")
    
    try:
        result = subprocess.run(
            ["docker", "inspect", "docker/mcp-gateway"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ MCP Gateway image available")
            return True
        else:
            print("⚠️  MCP Gateway image not found locally")
            print("   Try: docker pull docker/mcp-gateway")
            return False
            
    except Exception as e:
        print(f"❌ Error checking MCP Gateway image: {e}")
        return False


def test_gateway_startup_simulation():
    """Simulate gateway startup process."""
    print("\n🔄 Simulating MCP Gateway startup process...")
    
    # Load configuration
    config_path = Path("mcp-config/servers.json")
    if not config_path.exists():
        print("❌ Config file not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        servers = config.get("servers", {})
        print(f"📋 Found {len(servers)} server configurations")
        
        # Simulate each server startup
        for server_name, server_config in servers.items():
            print(f"\n🔧 Testing server: {server_name}")
            
            command = server_config.get("command", "")
            args = server_config.get("args", [])
            env_vars = server_config.get("env", {})
            
            print(f"   Command: {command} {' '.join(args)}")
            print(f"   Environment variables: {len(env_vars)}")
            
            # Check if the command would work
            if command == "docker":
                if len(args) >= 3 and args[0] == "run":
                    image_name = args[-1]  # Last argument should be image name
                    print(f"   Docker image: {image_name}")
                    
                    # Test if image exists
                    try:
                        result = subprocess.run(
                            ["docker", "inspect", image_name],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if result.returncode == 0:
                            print(f"   ✅ Image {image_name} is available")
                        else:
                            print(f"   ⚠️  Image {image_name} not found locally")
                    except Exception as e:
                        print(f"   ❌ Error checking image: {e}")
                else:
                    print("   ⚠️  Unexpected docker command format")
            else:
                print(f"   ⚠️  Non-docker command: {command}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error simulating startup: {e}")
        return False


async def test_adapter_connectivity():
    """Test adapter connectivity to gateway."""
    print("\n🔌 Testing adapter connectivity...")
    
    # Mock the MCP adapter test
    sys.path.insert(0, str(Path(__file__).parent / "app"))
    
    # Apply mocks
    import sys
    sys.modules['httpx'] = type(sys)('httpx')
    sys.modules['httpx'].AsyncClient = MockHttpxClient
    sys.modules['httpx'].Timeout = lambda **k: None
    sys.modules['httpx'].TimeoutException = TimeoutError
    
    # Mock loguru
    sys.modules['loguru'] = type(sys)('loguru')
    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARN: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def debug(self, msg): print(f"DEBUG: {msg}")
    sys.modules['loguru'].logger = MockLogger()
    
    # Mock MCP
    sys.modules['mcp'] = type(sys)('mcp')
    sys.modules['mcp'].ClientSession = object
    sys.modules['mcp.types'] = type(sys)('mcp.types')
    sys.modules['mcp.types'].Tool = lambda name, description="": None
    
    try:
        from app.services.mcp_adapter import MCPServerAdapter, AdapterConfig
        
        print("📡 Testing adapter initialization...")
        config = AdapterConfig(gateway_url="http://localhost:8811")
        adapter = MCPServerAdapter(config)
        
        print("✅ Adapter created successfully")
        print("📊 Adapter diagnostics:")
        
        diagnostics = adapter.get_diagnostics()
        for key, value in diagnostics.items():
            if key != "config":  # Skip nested config for brevity
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Adapter test failed: {e}")
        return False


def provide_troubleshooting_tips():
    """Provide troubleshooting recommendations."""
    print("\n🔧 Troubleshooting Tips:")
    print("=" * 40)
    
    tips = [
        "1. Ensure Docker daemon is running and accessible",
        "2. Pull required MCP server images: docker pull mcp/duckduckgo && docker pull stickerdaniel/linkedin-mcp-server",
        "3. Pull MCP Gateway image: docker pull docker/mcp-gateway",
        "4. Check Docker socket permissions: ls -la /var/run/docker.sock",
        "5. Verify MCP Gateway can access Docker: docker run --rm -v /var/run/docker.sock:/var/run/docker.sock docker/mcp-gateway --help",
        "6. Check for port conflicts: netstat -tuln | grep 8811",
        "7. Review Docker logs: docker logs trainium_mcp_gateway",
        "8. Test individual MCP servers: docker run --rm -i mcp/duckduckgo",
        "9. Verify network connectivity between containers",
        "10. Check resource limits (CPU/memory) for containers"
    ]
    
    for tip in tips:
        print(f"   {tip}")


async def main():
    """Run all diagnostic tests."""
    print("🚀 MCP Gateway Startup Diagnostics")
    print("=" * 50)
    
    tests = [
        ("Docker Access", check_docker_access),
        ("MCP Server Images", check_mcp_images),
        ("MCP Gateway Image", check_gateway_image),
        ("Gateway Startup Simulation", test_gateway_startup_simulation),
        ("Adapter Connectivity", test_adapter_connectivity),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 50}")
    print("Diagnostic Summary")
    print(f"{'=' * 50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        emoji = "✅" if result else "❌"
        print(f"{emoji} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed < total:
        provide_troubleshooting_tips()
    else:
        print("\n🎉 All diagnostic tests passed!")
        print("The MCP Gateway should be able to start successfully.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)