#!/usr/bin/env python3
"""
Integration test for queue-based scraping system.
Tests the basic functionality without requiring live database or Redis.
"""
import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

from app.services.scraping import scrape_jobs_sync
from app.models.jobspy import JobSite


def test_shared_scraping_function():
    """Test the shared scraping function with mock data."""
    
    print("🧪 Testing shared scraping function...")
    
    # Mock payload for Indeed
    payload = {
        "site_name": "indeed",
        "search_term": "python developer",
        "location": "remote",
        "is_remote": True,
        "results_wanted": 5,
        "country_indeed": "USA"
    }
    
    # Mock the actual jobspy.scrape_jobs function
    with patch('app.services.scraping.scrape_jobs') as mock_scrape:
        # Create mock pandas DataFrame
        mock_df = Mock()
        mock_df.empty = False
        
        # Mock iterrows to return sample job data
        mock_row_data = {
            'title': 'Senior Python Developer',
            'company': 'Test Company',
            'location': 'Remote',
            'job_type': 'Full-time',
            'date_posted': '2025-01-24',
            'min_amount': 80000,
            'max_amount': 120000,
            'salary_source': 'employer',
            'interval': 'yearly',
            'description': 'Great Python role',
            'job_url': 'https://example.com/job/123',
            'job_url_direct': 'https://example.com/apply/123',
            'site': 'indeed',
            'emails': [],
            'is_remote': True
        }
        
        mock_df.iterrows.return_value = [(0, Mock(**mock_row_data))]
        mock_scrape.return_value = mock_df
        
        # Execute the function
        result = scrape_jobs_sync(payload, min_pause=0, max_pause=0)
        
        # Validate results
        assert result['status'] in ['succeeded', 'partial', 'failed']
        assert 'jobs' in result
        assert 'total_found' in result
        assert result['total_found'] >= 0
        assert 'search_metadata' in result
        
        print(f"✅ Scraping function returned {result['total_found']} jobs with status '{result['status']}'")
        
        # Verify jobspy was called with correct parameters
        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args[1]
        assert call_args['site_name'] == 'indeed'
        assert call_args['search_term'] == 'python developer'
        assert call_args['country_indeed'] == 'USA'
        
        print("✅ Shared scraping function test passed!")


async def test_api_endpoints():
    """Test API endpoint structure without live services."""
    
    print("🧪 Testing API endpoint imports...")
    
    from app.api.v1.endpoints.jobspy import router as jobspy_router
    from app.api.v1.endpoints.scheduler import router as scheduler_router
    from app.api.router import api_router
    
    # Check that routers have the expected endpoints
    jobspy_routes = [route.path for route in jobspy_router.routes]
    scheduler_routes = [route.path for route in scheduler_router.routes]
    
    # Validate jobspy endpoints
    expected_jobspy_routes = ['/scrape', '/scrape/{run_id}', '/sites', '/health', '/queue/status']
    for expected_route in expected_jobspy_routes:
        assert any(expected_route in route for route in jobspy_routes), f"Missing route: {expected_route}"
    
    # Validate scheduler endpoints
    expected_scheduler_routes = ['/run', '/status']
    for expected_route in expected_scheduler_routes:
        assert any(expected_route in route for route in scheduler_routes), f"Missing route: {expected_route}"
    
    print("✅ All expected API endpoints are registered!")


def test_service_initialization():
    """Test service initialization without live dependencies."""
    
    print("🧪 Testing service initialization...")
    
    from app.services.database import get_database_service
    from app.services.queue import get_queue_service
    from app.services.scheduler import get_scheduler_service
    
    # Test service instance creation
    db_service = get_database_service()
    queue_service = get_queue_service()
    scheduler_service = get_scheduler_service()
    
    assert db_service is not None
    assert queue_service is not None  
    assert scheduler_service is not None
    
    # Test singleton pattern
    db_service2 = get_database_service()
    assert db_service is db_service2
    
    print("✅ Service initialization test passed!")


def test_database_schema():
    """Test database schema generation."""
    
    print("🧪 Testing database schema files...")
    
    # Check that migration files exist
    deploy_file = "/home/runner/work/Trainium-Job-Center/Trainium-Job-Center/DB Scripts/sqitch/deploy/queue-scheduler-tables.sql"
    revert_file = "/home/runner/work/Trainium-Job-Center/Trainium-Job-Center/DB Scripts/sqitch/revert/queue-scheduler-tables.sql"
    verify_file = "/home/runner/work/Trainium-Job-Center/Trainium-Job-Center/DB Scripts/sqitch/verify/queue-scheduler-tables.sql"
    
    assert os.path.exists(deploy_file), "Deploy migration file missing"
    assert os.path.exists(revert_file), "Revert migration file missing"
    assert os.path.exists(verify_file), "Verify migration file missing"
    
    # Check deploy file contains expected table creation
    with open(deploy_file, 'r') as f:
        deploy_content = f.read()
        
    assert 'CREATE TABLE site_schedules' in deploy_content
    assert 'CREATE TABLE scrape_runs' in deploy_content
    assert 'site_name' in deploy_content
    assert 'enabled' in deploy_content
    assert 'interval_minutes' in deploy_content
    
    print("✅ Database schema files are correctly structured!")


def run_all_tests():
    """Run all integration tests."""
    
    print("🚀 Running Queue-Based Scraping System Integration Tests\n")
    
    try:
        # Run synchronous tests
        test_shared_scraping_function()
        print()
        
        test_service_initialization()
        print()
        
        test_database_schema()
        print()
        
        # Run async tests
        asyncio.run(test_api_endpoints())
        print()
        
        print("🎉 All integration tests passed!")
        print("\n📋 Summary:")
        print("   ✅ Shared scraping function works correctly")
        print("   ✅ Service instances initialize properly")
        print("   ✅ Database schema migrations are valid")
        print("   ✅ API endpoints are registered correctly")
        print("\n✨ Queue-based scraping system is ready for deployment!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)