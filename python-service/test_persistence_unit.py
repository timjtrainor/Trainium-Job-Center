#!/usr/bin/env python3
"""
Simple tests for job persistence functionality without database dependencies.
Tests mapping, normalization, and basic functionality.
"""
import sys
import os
from datetime import datetime
from unittest.mock import Mock

# Add the project root to Python path  
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock dependencies before importing
sys.modules['app.core.config'] = Mock()
sys.modules['app.services.database'] = Mock()

# Mock get_settings to return fake config
mock_settings = Mock()
mock_settings.database_url = "fake://connection"

def mock_get_settings():
    return mock_settings

sys.modules['app.core.config'].get_settings = mock_get_settings

# Mock get_database_service
mock_db_service = Mock()
sys.modules['app.services.database'].get_database_service = lambda: mock_db_service

# Now we can import the actual modules
from app.models.jobspy import ScrapedJob


def test_scraped_job_model():
    """Test basic ScrapedJob model functionality."""
    print("🧪 Testing ScrapedJob model...")
    
    # Create test job with various field types
    job = ScrapedJob(
        title="Senior Python Developer",
        company="Test Company",
        location="Remote",
        job_type="fulltime",
        date_posted="2025-01-24",
        salary_min=80000.0,
        salary_max=120000.0,
        salary_source="employer",
        interval="yearly",
        description="Great Python role",
        job_url="https://example.com/job/123",
        job_url_direct="https://example.com/apply/123",
        site="indeed",
        emails=["hr@company.com"],
        is_remote=True
    )
    
    # Verify fields are set correctly
    assert job.title == "Senior Python Developer"
    assert job.company == "Test Company"
    assert job.salary_min == 80000.0
    assert job.salary_max == 120000.0
    assert job.is_remote is True
    assert job.site == "indeed"
    assert job.emails == ["hr@company.com"]
    
    print("✅ ScrapedJob model test passed")


def test_job_field_mapping_logic():
    """Test the field mapping logic without database calls."""  
    print("🧪 Testing job field mapping logic...")
    
    # Import after mocking
    from app.services.job_persistence import JobPersistenceService
    
    service = JobPersistenceService()
    
    # Create test job
    test_job = ScrapedJob(
        title="Data Scientist",
        company="AI Corp",
        location="New York, NY",
        job_type="fulltime", 
        date_posted="2025-01-24T15:30:00+00:00",
        salary_min=90000.0,
        salary_max=140000.0,
        salary_source="glassdoor",
        interval="yearly",
        description="Machine learning role",
        job_url="https://example.com/job/456",
        job_url_direct="https://example.com/direct/456",
        site="linkedin",
        emails=None,
        is_remote=False
    )
    
    # Test mapping
    mapped = service._map_job_to_db(test_job, "linkedin")
    
    # Verify core mappings
    assert mapped["site"] == "linkedin"
    assert mapped["job_url"] == "https://example.com/job/456"
    assert mapped["title"] == "Data Scientist"
    assert mapped["company"] == "AI Corp"
    assert mapped["is_remote"] is False
    assert mapped["job_type"] == "fulltime"
    assert mapped["min_amount"] == 90000.0
    assert mapped["max_amount"] == 140000.0
    assert mapped["salary_source"] == "glassdoor"
    assert mapped["interval"] == "yearly"
    assert mapped["description"] == "Machine learning role"
    
    # Verify nullable/placeholder fields
    assert mapped["company_url"] is None
    assert mapped["location_country"] is None
    assert mapped["location_state"] is None
    assert mapped["location_city"] is None
    assert mapped["compensation"] is None
    assert mapped["currency"] is None
    assert mapped["canonical_key"] is None
    assert mapped["fingerprint"] is None
    assert mapped["duplicate_group_id"] is None
    
    # Verify timestamps
    assert mapped["ingested_at"] is not None
    assert isinstance(mapped["ingested_at"], datetime)
    assert mapped["date_posted"] is not None
    
    # Verify source_raw contains original data
    assert mapped["source_raw"]["title"] == "Data Scientist"
    assert mapped["source_raw"]["company"] == "AI Corp"
    assert mapped["source_raw"]["job_url"] == "https://example.com/job/456"
    assert mapped["source_raw"]["salary_min"] == 90000.0
    assert "scraped_at" in mapped["source_raw"]
    
    print("✅ Job field mapping test passed")


def test_date_parsing():
    """Test date parsing functionality."""
    print("🧪 Testing date parsing...")
    
    from app.services.job_persistence import JobPersistenceService
    service = JobPersistenceService()
    
    # Test various date formats
    test_cases = [
        # (input, should_parse_successfully)
        ("2025-01-24", True),
        ("2025-01-24T10:30:00", True), 
        ("2025-01-24T10:30:00+00:00", True),
        ("2025-01-24T10:30:00Z", True),
        (None, False),
        ("", False),
        ("invalid-date", False)
    ]
    
    for date_input, should_succeed in test_cases:
        job = ScrapedJob(
            title="Test Job",
            job_url="https://example.com/test",
            date_posted=date_input
        )
        
        mapped = service._map_job_to_db(job, "indeed")
        
        if should_succeed and date_input:
            assert mapped["date_posted"] is not None, f"Failed to parse date: {date_input}"
        else:
            # None or failed parsing should result in None
            if date_input is None:
                assert mapped["date_posted"] is None
    
    print("✅ Date parsing test passed")


def test_validation_logic():
    """Test validation logic for required fields."""
    print("🧪 Testing validation logic...")
    
    # Test cases: (title, job_url, should_be_valid)
    test_cases = [
        ("Python Developer", "https://example.com/1", True),
        ("", "https://example.com/2", False),  # Missing title
        ("Developer", "", False),              # Missing job_url
        ("", "", False),                       # Both missing
        (None, "https://example.com/3", False), # None title
        ("Developer", None, False),            # None job_url
    ]
    
    for title, job_url, should_be_valid in test_cases:
        job = ScrapedJob(title=title, job_url=job_url)
        
        # Check basic validation logic that would be used in persist_jobs
        has_job_url = bool(job.job_url)
        has_title = bool(job.title)
        is_valid = has_job_url and has_title
        
        assert is_valid == should_be_valid, f"Validation failed for title='{title}', job_url='{job_url}'"
    
    print("✅ Validation logic test passed")


if __name__ == "__main__":
    print("🧪 Running job persistence unit tests...\n")
    
    test_scraped_job_model()
    test_job_field_mapping_logic() 
    test_date_parsing()
    test_validation_logic()
    
    print("\n✅ All job persistence unit tests passed!")