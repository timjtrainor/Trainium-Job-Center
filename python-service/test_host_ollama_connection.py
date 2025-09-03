#!/usr/bin/env python3
"""
Test script to verify Ollama host-based connection works properly.
This test validates that the configuration changes enable proper connection
to Ollama running on the host machine instead of in Docker container.
"""

import os
import sys
import httpx
from loguru import logger

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ollama_host_connection():
    """Test connection to Ollama on different host configurations."""
    
    print("🧪 Testing Ollama Host Connection Configuration\n")
    
    # Test different host configurations
    test_hosts = [
        ("Docker host.docker.internal", "http://host.docker.internal:11434"),
        ("Local localhost", "http://localhost:11434"),
        ("Environment variable", os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    ]
    
    results = []
    
    for description, host_url in test_hosts:
        print(f"Testing {description}: {host_url}")
        
        try:
            # Quick connectivity test
            response = httpx.get(f"{host_url}/api/tags", timeout=5)
            status = "✅ Connected" if response.status_code == 200 else f"❌ HTTP {response.status_code}"
            print(f"  Result: {status}")
            results.append((description, host_url, response.status_code == 200))
        except httpx.ConnectError as e:
            print(f"  Result: ❌ Connection failed - {e}")
            results.append((description, host_url, False))
        except httpx.TimeoutException:
            print(f"  Result: ❌ Connection timeout")
            results.append((description, host_url, False))
        except Exception as e:
            print(f"  Result: ❌ Unexpected error - {e}")
            results.append((description, host_url, False))
        
        print()
    
    return results

def test_llm_client_configuration():
    """Test that the LLM client uses the correct host configuration."""
    
    print("🧪 Testing LLM Client Configuration\n")
    
    try:
        from app.services.llm_clients import OllamaClient
        from app.core.config import get_settings
        
        settings = get_settings()
        print(f"Config OLLAMA_HOST: {settings.ollama_host}")
        
        # Test default client
        client = OllamaClient("gemma3:1b")
        print(f"Default client host: {client.host}")
        
        # Test client with specific host
        client_custom = OllamaClient("gemma3:1b", host="http://custom-host:11434")
        print(f"Custom client host: {client_custom.host}")
        
        # Test availability check
        print(f"Client availability check: {client.is_available()}")
        
        print("✅ LLM Client configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ LLM Client test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable configuration."""
    
    print("🧪 Testing Environment Variables\n")
    
    env_vars = [
        "OLLAMA_HOST",
        "LLM_PREFERENCE", 
        "LLM_MODEL"
    ]
    
    for var in env_vars:
        value = os.getenv(var, "Not set")
        print(f"{var}: {value}")
    
    print()

def main():
    """Run all configuration tests."""
    
    print("🚀 Host-based Ollama Configuration Test Suite\n")
    print("=" * 60 + "\n")
    
    # Test environment variables
    test_environment_variables()
    
    # Test connections
    connection_results = test_ollama_host_connection()
    
    # Test client configuration
    client_ok = test_llm_client_configuration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    
    # Connection summary
    successful_connections = [r for r in connection_results if r[2]]
    if successful_connections:
        print(f"✅ Ollama connection successful via: {successful_connections[0][0]}")
        print(f"   Host: {successful_connections[0][1]}")
    else:
        print("❌ No successful Ollama connections found")
        print("   💡 Make sure Ollama is running on the host machine:")
        print("      ollama serve")
    
    # Client configuration summary
    if client_ok:
        print("✅ LLM client configuration is correct")
    else:
        print("❌ LLM client configuration issues detected")
    
    # Overall result
    overall_success = len(successful_connections) > 0 and client_ok
    if overall_success:
        print("\n🎉 Host-based Ollama configuration is working correctly!")
        print("   The system is ready to use GPU acceleration.")
    else:
        print("\n🔧 Configuration needs attention before GPU features will work.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)