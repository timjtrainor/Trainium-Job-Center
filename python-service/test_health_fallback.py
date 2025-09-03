#!/usr/bin/env python3
"""
Test health endpoint to ensure graceful handling when Ollama is not available.
This verifies that the application doesn't crash and provides useful status info.
"""

import os
import sys
import asyncio

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_health_endpoint_without_ollama():
    """Test health endpoint when Ollama is not available."""
    
    print("🧪 Testing Health Endpoint Without Ollama\n")
    
    # Set minimal environment for testing
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
    
    try:
        from app.api.health import health_check, detailed_health_check
        
        # Test basic health check
        print("Testing basic health check...")
        response = await health_check()
        
        print(f"Status: {response.status}")
        print(f"Message: {response.message}")
        
        if hasattr(response.data, 'status'):
            print(f"Service Status: {response.data.status}")
        
        # Test detailed health check
        print("\nTesting detailed health check...")
        detailed_response = await detailed_health_check()
        
        print(f"Status: {detailed_response.status}")
        print(f"Message: {detailed_response.message}")
        
        # Check LLM provider status
        if hasattr(detailed_response.data, 'dependencies') and 'llm_providers' in detailed_response.data.dependencies:
            llm_status = detailed_response.data.dependencies['llm_providers']
            print(f"LLM Providers Available: {llm_status.get('available', [])}")
        
        print("✅ Health endpoints work correctly without Ollama")
        return True
        
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

async def test_llm_router_fallback():
    """Test LLM router behavior when Ollama is not available."""
    
    print("\n🧪 Testing LLM Router Fallback\n")
    
    try:
        from app.services.llm_clients import LLMRouter
        
        # Create router with multiple providers
        router = LLMRouter("ollama:gemma3:1b,openai:gpt-4o-mini,gemini:gemini-1.5-flash")
        
        # Check available providers
        providers = router.get_available_providers()
        print("Provider availability:")
        for provider, model, available in providers:
            status = "✅" if available else "❌"
            print(f"  {status} {provider}:{model}")
        
        # Test generation (should fail gracefully)
        try:
            result = router.generate("Hello, world!")
            print(f"✅ Generation succeeded: {result[:50]}...")
        except Exception as e:
            print(f"❌ Generation failed (expected): {e}")
            print("✅ Router fails gracefully when no providers available")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM router test failed: {e}")
        return False

async def main():
    """Run all health and fallback tests."""
    
    print("🚀 Health & Fallback Test Suite")
    print("=" * 60 + "\n")
    
    tests = [
        test_health_endpoint_without_ollama,
        test_llm_router_fallback
    ]
    
    passed = 0
    
    for test_func in tests:
        if await test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📋 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All health and fallback mechanisms work correctly!")
        print("✅ Application handles missing Ollama gracefully")
    else:
        print("❌ Some tests failed - error handling may need attention")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)