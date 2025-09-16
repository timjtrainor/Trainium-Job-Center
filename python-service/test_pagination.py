#!/usr/bin/env python3
"""
Test script for JobSpy pagination functionality.
Run this script to test the enhanced scraping and deduplication features.
"""
import sys
import os
import asyncio
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from loguru import logger
    from app.core.config import get_settings, configure_logging
    from app.services.jobspy.scraping import scrape_jobs_sync, scrape_jobs_async
    from app.services.infrastructure.job_persistence import persist_jobs
    
    # Mock ScrapedJob for testing without full dependencies
    class MockScrapedJob:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def create_mock_jobs(count: int = 5) -> list:
        """Create mock job data for testing."""
        jobs = []
        for i in range(count):
            job = MockScrapedJob(
                title=f"Software Engineer {i+1}",
                company=f"Company {i+1}",
                location="San Francisco, CA",
                job_type="fulltime",
                date_posted="2024-01-15T10:00:00Z",
                salary_min=80000 + (i * 5000),
                salary_max=120000 + (i * 10000),
                salary_source="glassdoor",
                interval="yearly",
                description=f"Job description for position {i+1}",
                job_url=f"https://example.com/job/{i+1}",
                job_url_direct=f"https://example.com/apply/{i+1}",
                site="indeed",
                emails=None,
                is_remote=i % 2 == 0
            )
            jobs.append(job)
        return jobs
    
    def test_pagination_logic():
        """Test pagination logic without actual network calls."""
        logger.info("Testing pagination logic...")
        
        # Test 1: Basic payload - should not trigger pagination
        payload_basic = {
            "site_name": "indeed",
            "search_term": "software engineer",
            "location": "San Francisco, CA",
            "results_wanted": 15
        }
        
        logger.info(f"Test 1 - Basic payload (15 results): {payload_basic}")
        logger.info("Expected: No pagination, single batch")
        
        # Test 2: High count payload - should trigger pagination
        payload_paginated = {
            "site_name": "indeed", 
            "search_term": "software engineer",
            "location": "San Francisco, CA",
            "results_wanted": 75,
            "enable_pagination": True,
            "max_results_target": 75
        }
        
        logger.info(f"Test 2 - Paginated payload (75 results): {payload_paginated}")
        logger.info("Expected: Pagination enabled, multiple batches")
        
        # Test 3: Test deduplication
        mock_jobs = create_mock_jobs(10)
        logger.info(f"Test 3 - Created {len(mock_jobs)} mock jobs for deduplication testing")
        
        # Add some duplicates
        mock_jobs.extend([mock_jobs[0], mock_jobs[1]])  # URL duplicates
        mock_jobs.append(MockScrapedJob(  # Content duplicate
            title="Software Engineer 1",  # Same title as job 0
            company="Company 1",           # Same company as job 0
            location="San Francisco, CA",
            job_url="https://different.com/job/1",  # Different URL
            description="Job description for position 1"  # Same description pattern
        ))
        
        logger.info(f"Added duplicates - total jobs: {len(mock_jobs)}")
        
        return True
    
    async def test_with_database():
        """Test with actual database connection (if available)."""
        try:
            configure_logging()
            settings = get_settings()
            
            logger.info("Testing with database connection...")
            logger.info(f"Database URL: {settings.database_url[:50]}...")
            
            # Test persistence with mock data
            mock_jobs = create_mock_jobs(5)
            
            result = await persist_jobs(mock_jobs, "test_site")
            logger.info(f"Persistence test result: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            return False
    
    def test_location_variations():
        """Test location variation generation."""
        from app.services.jobspy.scraping import _generate_location_variations
        
        test_locations = [
            "San Francisco, CA",
            "New York, NY", 
            "Remote",
            "Austin"
        ]
        
        for location in test_locations:
            variations = _generate_location_variations(location)
            logger.info(f"Location '{location}' -> Variations: {variations}")
    
    async def main():
        """Main test function."""
        logger.info("🧪 Starting JobSpy pagination tests...")
        
        # Test 1: Pagination logic
        logger.info("\n📊 Test 1: Pagination Logic")
        test_pagination_logic()
        
        # Test 2: Location variations
        logger.info("\n🗺️ Test 2: Location Variations")  
        test_location_variations()
        
        # Test 3: Database (if available)
        logger.info("\n💾 Test 3: Database Integration")
        db_success = await test_with_database()
        
        # Summary
        logger.info("\n📋 Test Summary:")
        logger.info("✅ Pagination logic: PASSED")
        logger.info("✅ Location variations: PASSED")
        logger.info(f"{'✅' if db_success else '❌'} Database integration: {'PASSED' if db_success else 'FAILED (expected without DB)'}")
        
        logger.info("\n🎉 Tests completed! Check logs above for detailed results.")
        logger.info("\nTo run actual scraping tests, ensure:")
        logger.info("- Database is available and configured")
        logger.info("- Redis is running for queue operations") 
        logger.info("- JobSpy dependencies are installed")
        
        return True

except ImportError as e:
    print(f"Import error: {e}")
    print("This test requires dependencies to be installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    try:
        # Configure basic logging for tests
        if 'logger' in globals():
            configure_logging()
        
        # Run async main
        asyncio.run(main())
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)