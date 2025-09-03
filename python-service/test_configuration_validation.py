#!/usr/bin/env python3
"""
Simple validation test to ensure configuration changes work correctly.
This test validates the LLM client configuration without external dependencies.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_llm_router_parsing():
    """Test LLM router parses preferences correctly."""
    
    from app.services.llm_clients import LLMRouter
    
    print("🧪 Testing LLM Router Preference Parsing")
    
    # Test default preferences 
    router = LLMRouter("ollama:gemma3:1b,openai:gpt-4o-mini,gemini:gemini-1.5-flash")
    
    expected_providers = [
        ("ollama", "gemma3:1b"),
        ("openai", "gpt-4o-mini"), 
        ("gemini", "gemini-1.5-flash")
    ]
    
    assert router.providers == expected_providers, f"Expected {expected_providers}, got {router.providers}"
    print("✅ LLM router preference parsing works correctly")

def test_ollama_client_host_configuration():
    """Test Ollama client uses correct host configuration."""
    
    from app.services.llm_clients import OllamaClient
    
    print("🧪 Testing Ollama Client Host Configuration")
    
    # Test default host
    client1 = OllamaClient("gemma3:1b")
    assert client1.host == "http://localhost:11434", f"Expected localhost, got {client1.host}"
    print("✅ Default host is localhost:11434")
    
    # Test custom host
    client2 = OllamaClient("gemma3:1b", host="http://custom-host:11434")
    assert client2.host == "http://custom-host:11434", f"Expected custom-host, got {client2.host}"
    print("✅ Custom host configuration works")

def test_client_factory():
    """Test client factory creates correct clients."""
    
    from app.services.llm_clients import create_llm_client
    
    print("🧪 Testing Client Factory")
    
    # Test Ollama client creation
    ollama_client = create_llm_client("ollama", "gemma3:1b", host="http://test-host:11434")
    assert ollama_client.provider == "ollama"
    assert ollama_client.model == "gemma3:1b" 
    assert ollama_client.host == "http://test-host:11434"
    print("✅ Ollama client factory works with custom host")

def test_config_defaults():
    """Test configuration defaults are correct."""
    
    from app.core.config import get_settings
    
    print("🧪 Testing Configuration Defaults")
    
    settings = get_settings()
    
    # Check Ollama host default  
    assert settings.ollama_host == "http://localhost:11434", f"Expected localhost, got {settings.ollama_host}"
    print("✅ Config default OLLAMA_HOST is localhost:11434")
    
    # Check LLM preference includes Ollama
    assert "ollama:" in settings.llm_preference, f"ollama not found in {settings.llm_preference}"
    print("✅ LLM preference includes Ollama provider")

def main():
    """Run all validation tests."""
    
    print("🚀 Configuration Validation Test Suite")
    print("=" * 60 + "\n")
    
    # Set minimal environment for testing
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
    
    tests = [
        test_llm_router_parsing,
        test_ollama_client_host_configuration, 
        test_client_factory,
        test_config_defaults
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
            print()
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
            print()
    
    print("=" * 60)
    print(f"📋 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All configuration validation tests passed!")
        print("✅ Host-based Ollama configuration is working correctly")
        return True
    else:
        print("❌ Some tests failed - configuration may need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)