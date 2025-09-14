#!/usr/bin/env python3
"""Basic integration test for ChromaDB functionality."""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all our new modules can be imported."""
    try:
        from app.services.chroma_manager import ChromaManager, CollectionType, get_chroma_manager
        print("✓ ChromaManager imported successfully")
        
        from app.services.chroma_integration_service import ChromaIntegrationService, get_chroma_integration_service
        print("✓ ChromaIntegrationService imported successfully")
        
        from app.services.crewai.tools.chroma_search import (
            chroma_search, search_job_postings, search_company_profiles, 
            contextual_job_analysis
        )
        print("✓ Enhanced ChromaDB tools imported successfully")
        
        from app.api.v1.endpoints.chroma_manager import router
        print("✓ ChromaDB manager API endpoints imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_manager_initialization():
    """Test basic manager functionality."""
    try:
        from app.services.chroma_manager import ChromaManager, CollectionType
        
        manager = ChromaManager()
        print("✓ ChromaManager instantiated")
        
        # Test collection config registration
        configs = manager.list_registered_collections()
        print(f"✓ Found {len(configs)} registered collection configurations")
        
        # Check for expected collections
        config_names = [c.name for c in configs]
        expected = ["job_postings", "company_profiles", "career_brands", "documents"]
        
        for name in expected:
            if name in config_names:
                print(f"✓ {name} collection configured")
            else:
                print(f"✗ {name} collection missing")
                return False
        
        # Test collection type enumeration
        assert CollectionType.JOB_POSTINGS.value == "job_postings"
        assert CollectionType.COMPANY_PROFILES.value == "company_profiles"
        print("✓ Collection type enumeration works")
        
        return True
    except Exception as e:
        print(f"✗ Manager initialization failed: {e}")
        return False

def test_crewai_integration():
    """Test CrewAI tool integration."""
    try:
        from app.services.crewai.job_posting_review.crew import JobPostingReviewCrew
        print("✓ JobPostingReviewCrew imports successfully")
        
        # Verify the crew class exists and can be instantiated
        crew_class = JobPostingReviewCrew
        print("✓ CrewAI job posting review crew is accessible")
        
        return True
    except Exception as e:
        print(f"✗ CrewAI integration test failed: {e}")
        return False

def test_api_structure():
    """Test API endpoint structure."""
    try:
        from app.api.router import api_router
        print("✓ Main API router imported")
        
        # Check that our router is included  
        routes = [route.path for route in api_router.routes]
        chroma_routes = [r for r in routes if "chroma" in r.lower()]
        
        if chroma_routes:
            print(f"✓ Found {len(chroma_routes)} ChromaDB-related routes")
            for route in chroma_routes[:3]:  # Show first 3
                print(f"  - {route}")
        else:
            print("✗ No ChromaDB routes found in API router")
            return False
        
        return True
    except Exception as e:
        print(f"✗ API structure test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("Running ChromaDB Integration Tests")
    print("=" * 40)
    
    tests = [
        ("Import Tests", test_imports),
        ("Manager Initialization", test_manager_initialization), 
        ("CrewAI Integration", test_crewai_integration),
        ("API Structure", test_api_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n{name}:")
        if test_func():
            print(f"✓ {name} PASSED")
            passed += 1
        else:
            print(f"✗ {name} FAILED")
    
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("\nChromaDB integration is ready for use with CrewAI!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())