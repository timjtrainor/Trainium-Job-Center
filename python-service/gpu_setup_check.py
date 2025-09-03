#!/usr/bin/env python3
"""
GPU-enabled Ollama Setup Verification Script

This script helps developers verify that their host-based Ollama setup
is working correctly and ready for GPU-accelerated inference.
"""

import subprocess
import sys
import httpx
from loguru import logger

def check_ollama_installation():
    """Check if Ollama is installed on the host."""
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Ollama installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Ollama command failed")
            return False
    except FileNotFoundError:
        print("❌ Ollama not found. Install with: curl -fsSL https://ollama.ai/install.sh | sh")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Ollama command timed out")
        return False

def check_ollama_running():
    """Check if Ollama service is running."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service is running on localhost:11434")
            return True
        else:
            print(f"❌ Ollama service returned HTTP {response.status_code}")
            return False
    except httpx.ConnectError:
        print("❌ Cannot connect to Ollama service. Start with: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama service: {e}")
        return False

def check_required_model():
    """Check if the required model (gemma3:1b) is available."""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            if "gemma3:1b" in result.stdout:
                print("✅ Model gemma3:1b is available")
                return True
            else:
                print("❌ Model gemma3:1b not found. Pull with: ollama pull gemma3:1b")
                return False
        else:
            print("❌ Failed to list Ollama models")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Ollama list command timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def check_gpu_availability():
    """Check if GPU is available for Ollama."""
    try:
        # Try to detect NVIDIA GPU
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ NVIDIA GPU detected (nvidia-smi working)")
            gpu_info = [line for line in result.stdout.split('\n') if 'NVIDIA' in line]
            if gpu_info:
                print(f"   GPU: {gpu_info[0].strip()}")
            return True
        else:
            print("⚠️  nvidia-smi not working (GPU may not be available)")
            return False
    except FileNotFoundError:
        print("⚠️  nvidia-smi not found (no NVIDIA GPU or drivers not installed)")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️  nvidia-smi timed out")
        return False

def test_inference():
    """Test basic inference with Ollama."""
    if not check_ollama_running():
        return False
    
    try:
        print("🧪 Testing basic inference...")
        result = subprocess.run([
            "ollama", "generate", "gemma3:1b", 
            "Write a one-sentence hello message:"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            print("✅ Basic inference test passed")
            print(f"   Response: {result.stdout.strip()[:100]}...")
            return True
        else:
            print("❌ Inference test failed")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Inference test timed out")
        return False
    except Exception as e:
        print(f"❌ Inference test error: {e}")
        return False

def main():
    """Run the complete GPU setup verification."""
    
    print("🚀 GPU-enabled Ollama Setup Verification")
    print("=" * 60 + "\n")
    
    checks = [
        ("Ollama Installation", check_ollama_installation),
        ("Ollama Service", check_ollama_running),
        ("Required Model", check_required_model),
        ("GPU Availability", check_gpu_availability),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"🔍 Checking {name}...")
        if check_func():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📋 Setup Status: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Perfect! Your GPU-enabled Ollama setup is ready!")
        
        # Run inference test as bonus
        print("\n🧪 Running inference test...")
        if test_inference():
            print("🚀 All systems go! Ready for GPU-accelerated inference.")
        else:
            print("⚠️  Setup looks good but inference test failed.")
            
    elif passed >= 3:  # Essential checks passed
        print("✅ Core setup is working. GPU may need attention.")
        print("\n💡 Tips for GPU setup:")
        print("   - Install NVIDIA drivers if you have an NVIDIA GPU")
        print("   - Restart Ollama after installing GPU drivers")
        
    else:
        print("❌ Setup needs attention before GPU features will work.")
        print("\n📖 Quick Setup Guide:")
        print("   1. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
        print("   2. Pull model: ollama pull gemma3:1b")
        print("   3. Start service: ollama serve")
        print("   4. Run this script again to verify")
    
    return passed >= 3  # At least core functionality working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)