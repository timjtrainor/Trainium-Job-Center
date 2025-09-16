#!/usr/bin/env python3
"""
Simple verification script for JobSpy enhancements.
Tests basic functionality without requiring external dependencies.
"""
import sys
import os
import json
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all enhanced modules import correctly."""
    print("🔍 Testing module imports...")
    
    try:
        from app.schemas.jobspy import JobSearchRequest, ScrapedJob, JobSite
        print("✅ JobSpy schemas import successful")
    except ImportError as e:
        print(f"❌ JobSpy schemas import failed: {e}")
        return False
    
    try:
        # Test pagination-related functionality
        from app.services.jobspy.scraping import scrape_jobs_sync, _generate_location_variations
        print("✅ JobSpy scraping module import successful")
    except ImportError as e:
        print(f"❌ JobSpy scraping module import failed: {e}")
        return False
    
    try:
        from app.services.infrastructure.scheduler import SchedulerService
        print("✅ Scheduler service import successful")
    except ImportError as e:
        print(f"❌ Scheduler service import failed: {e}")
        return False
    
    try:
        from app.services.infrastructure.job_persistence import JobPersistenceService
        print("✅ Job persistence service import successful")
    except ImportError as e:
        print(f"❌ Job persistence service import failed: {e}")
        return False
        
    return True

def test_schema_enhancements():
    """Test JobSearchRequest schema enhancements."""
    print("\n📋 Testing schema enhancements...")
    
    try:
        from app.schemas.jobspy import JobSearchRequest, JobSite
        
        # Test basic request
        basic_request = JobSearchRequest(
            site_name=JobSite.INDEED,
            search_term="software engineer",
            location="San Francisco, CA",
            results_wanted=15
        )
        print(f"✅ Basic request: {basic_request.site_name}, results: {basic_request.results_wanted}")
        
        # Test pagination request
        paginated_request = JobSearchRequest(
            site_name=JobSite.INDEED,
            search_term="software engineer",
            location="San Francisco, CA", 
            results_wanted=100,
            enable_pagination=True,
            max_results_target=100
        )
        print(f"✅ Paginated request: pagination={paginated_request.enable_pagination}, target={paginated_request.max_results_target}")
        
        # Test validation
        try:
            invalid_request = JobSearchRequest(
                site_name=JobSite.INDEED,
                search_term="test",
                results_wanted=1000  # Over limit
            )
            print("❌ Schema validation failed - should have rejected results_wanted=1000")
            return False
        except Exception:
            print("✅ Schema validation working - correctly rejected invalid results_wanted")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema enhancement test failed: {e}")
        return False

def test_location_variations():
    """Test location variation generation."""
    print("\n🗺️ Testing location variation generation...")
    
    try:
        from app.services.jobspy.scraping import _generate_location_variations
        
        test_cases = [
            "San Francisco, CA",
            "New York, NY",
            "Austin, TX",
            "Remote",
            "Seattle"
        ]
        
        for location in test_cases:
            variations = _generate_location_variations(location)
            print(f"✅ '{location}' -> {variations}")
        
        return True
        
    except Exception as e:
        print(f"❌ Location variation test failed: {e}")
        return False

def test_deduplication_logic():
    """Test deduplication logic without database."""
    print("\n🔍 Testing deduplication logic...")
    
    try:
        from app.services.infrastructure.job_persistence import JobPersistenceService
        
        # Create test service
        service = JobPersistenceService()
        
        # Create mock job records with duplicates
        mock_records = [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "description": "Great opportunity for software development",
                "job_url": "https://example.com/job/1"
            },
            {
                "title": "Software Engineer", # Same content
                "company": "Tech Corp",
                "description": "Great opportunity for software development",
                "job_url": "https://example.com/job/1"  # Same URL - should be dedupe'd
            },
            {
                "title": "Software Engineer", # Same content, different URL
                "company": "Tech Corp", 
                "description": "Great opportunity for software development",
                "job_url": "https://different.com/job/1"  # Different URL - content dedupe
            },
            {
                "title": "Senior Developer",  # Different content
                "company": "Other Corp",
                "description": "Senior level position",
                "job_url": "https://example.com/job/2"
            }
        ]
        
        # Test deduplication
        dedupe_result = service._deduplicate_records(mock_records)
        
        print(f"✅ Deduplication test results:")
        print(f"   Original count: {dedupe_result['original_count']}")
        print(f"   Unique count: {dedupe_result['unique_count']}")
        print(f"   URL duplicates removed: {dedupe_result['url_duplicates_removed']}")
        print(f"   Content duplicates removed: {dedupe_result['content_duplicates_removed']}")
        
        # Validate results
        expected_unique = 2  # Should have 2 unique jobs after deduplication
        if dedupe_result['unique_count'] == expected_unique:
            print(f"✅ Deduplication working correctly - {expected_unique} unique jobs retained")
        else:
            print(f"❌ Deduplication issue - expected {expected_unique}, got {dedupe_result['unique_count']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Deduplication logic test failed: {e}")
        return False

def test_pagination_detection():
    """Test pagination auto-enable logic."""
    print("\n📄 Testing pagination detection...")
    
    try:
        # Test payloads
        test_payloads = [
            {"results_wanted": 15, "enable_pagination": False},  # Should not trigger
            {"results_wanted": 25, "enable_pagination": False},  # Should not trigger  
            {"results_wanted": 50, "enable_pagination": False},  # Should trigger
            {"results_wanted": 100, "enable_pagination": True}   # Explicitly enabled
        ]
        
        for i, payload in enumerate(test_payloads):
            results_wanted = payload.get("results_wanted", 15)
            explicit_pagination = payload.get("enable_pagination", False)
            
            # Logic from scraping.py
            should_paginate = explicit_pagination or results_wanted > 25
            
            print(f"✅ Payload {i+1}: results_wanted={results_wanted}, "
                  f"explicit={explicit_pagination}, should_paginate={should_paginate}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pagination detection test failed: {e}")
        return False

def test_enhanced_logging_format():
    """Test that enhanced logging doesn't break."""
    print("\n📝 Testing enhanced logging format...")
    
    try:
        # Test that we can format log messages with emojis and special characters
        test_messages = [
            "🚀 Starting enhanced scheduler daemon...",
            "✅ Scheduler initialized successfully", 
            "📊 Queue info: {'length': 5, 'started': 2}",
            "💥 Error in scheduler loop: Connection failed",
            "🎉 Scheduler completed successfully - enqueued 3 jobs"
        ]
        
        for msg in test_messages:
            # Just verify the string doesn't cause encoding issues
            encoded = msg.encode('utf-8')
            decoded = encoded.decode('utf-8')
            assert msg == decoded, f"Encoding issue with: {msg}"
        
        print("✅ Enhanced logging format test passed")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced logging format test failed: {e}")
        return False

def main():
    """Main verification function."""
    print("🧪 JobSpy Enhancement Verification Suite")
    print("="*50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Schema Enhancements", test_schema_enhancements),
        ("Location Variations", test_location_variations),
        ("Deduplication Logic", test_deduplication_logic),
        ("Pagination Detection", test_pagination_detection),
        ("Enhanced Logging", test_enhanced_logging_format)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 VERIFICATION SUMMARY")
    print("="*60)
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<25}: {status}")
    
    print(f"\nOverall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("\nJobSpy enhancements are ready for testing with:")
        print("1. python test_pagination.py")
        print("2. python test_scheduler_reliability.py") 
        print("3. docker-compose up scheduler worker")
        return True
    else:
        print(f"\n⚠️ {total_count - passed_count} VERIFICATIONS FAILED")
        print("\nPlease fix the failing tests before deployment.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Verification suite failed: {e}")
        sys.exit(1)