#!/usr/bin/env python3
"""
Tests for job persistence functionality.
Tests mapping, normalization, idempotency, and error handling.
"""
import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.jobspy import ScrapedJob
from app.services.infrastructure.job_persistence import JobPersistenceService, persist_jobs


def test_job_mapping():
    """Test mapping of ScrapedJob to database fields."""
    print("🧪 Testing job field mapping...")
    
    # Create test scraped job
    test_job = ScrapedJob(
        title="Senior Python Developer",
        company="Test Company", 
        location="Remote",
        job_type="fulltime",
        date_posted="2025-01-24T10:30:00",
        salary_min=80000.0,
        salary_max=120000.0,
        salary_source="employer",
        interval="yearly",
        description="Great Python role with remote work",
        job_url="https://example.com/job/123",
        job_url_direct="https://example.com/apply/123",
        site="indeed",
        emails=["hr@company.com"],
        is_remote=True
    )
    
    # Create service instance and test mapping
    service = JobPersistenceService()
    mapped = service._map_job_to_db(test_job, "indeed")
    
    # Verify core fields
    assert mapped["site"] == "indeed"
    assert mapped["job_url"] == "https://example.com/job/123"
    assert mapped["title"] == "Senior Python Developer"
    assert mapped["company"] == "Test Company"
    assert mapped["is_remote"] is True
    assert mapped["job_type"] == "fulltime"
    assert mapped["min_amount"] == 80000.0
    assert mapped["max_amount"] == 120000.0
    assert mapped["interval"] == "yearly"
    assert mapped["salary_source"] == "employer"
    assert mapped["description"] == "Great Python role with remote work"
    
    # Verify nullable future fields
    assert mapped["company_url"] is None
    assert mapped["location_country"] is None
    assert mapped["compensation"] is None
    assert mapped["canonical_key"] is None
    
    # Verify source_raw contains original data
    assert mapped["source_raw"]["title"] == "Senior Python Developer"
    assert mapped["source_raw"]["job_url"] == "https://example.com/job/123"
    assert "scraped_at" in mapped["source_raw"]
    
    # Verify timestamps
    assert mapped["ingested_at"] is not None
    assert mapped["date_posted"] is not None
    
    print("✅ Job mapping test passed")


def test_bad_input_handling():
    """Test error handling for invalid job records."""
    print("🧪 Testing bad input handling...")
    
    # Test cases: missing job_url, missing title, both missing
    bad_jobs = [
        ScrapedJob(title="Python Dev", job_url=""),  # Empty job_url
        ScrapedJob(title="", job_url="https://example.com/1"),  # Empty title  
        ScrapedJob(title="", job_url=""),  # Both empty
        ScrapedJob(title="Good Job", job_url="https://example.com/good")  # Good record
    ]
    
    service = JobPersistenceService()
    
    # Mock the database connection and methods
    mock_conn = AsyncMock()
    service.db_service = Mock()
    service.db_service.initialized = True
    service.db_service.pool = Mock()
    service.db_service.pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    service.db_service.pool.acquire.return_value.__aexit__ = AsyncMock()
    mock_conn.transaction.return_value.__aenter__ = AsyncMock()
    mock_conn.transaction.return_value.__aexit__ = AsyncMock()
    
    # Mock _upsert_job to return "inserted" for valid jobs
    service._upsert_job = AsyncMock(return_value="inserted")
    
    # Run the test
    async def run_test():
        result = await service.persist_jobs(bad_jobs, "indeed")
        
        # Should have 1 successful insert, 3 errors
        assert result["inserted"] == 1
        assert result["skipped_duplicates"] == 0
        assert len(result["errors"]) == 3
        
        # Verify error messages mention missing fields
        errors_str = " ".join(result["errors"])
        assert "missing job_url" in errors_str
        assert "missing title" in errors_str
    
    asyncio.run(run_test())
    print("✅ Bad input handling test passed")


def test_idempotency():
    """Test that duplicate records are handled properly."""
    print("🧪 Testing idempotency...")
    
    # Create test job
    test_job = ScrapedJob(
        title="Python Developer",
        job_url="https://example.com/job/duplicate-test",
        company="Test Corp",
        site="indeed"
    )
    
    service = JobPersistenceService()
    
    # Mock database connection
    mock_conn = AsyncMock()
    service.db_service = Mock()
    service.db_service.initialized = True
    service.db_service.pool = Mock()
    service.db_service.pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    service.db_service.pool.acquire.return_value.__aexit__ = AsyncMock()
    mock_conn.transaction.return_value.__aenter__ = AsyncMock()
    mock_conn.transaction.return_value.__aexit__ = AsyncMock()
    
    # First call returns "inserted", second returns "duplicate"
    service._upsert_job = AsyncMock(side_effect=["inserted", "duplicate"])
    
    async def run_test():
        # First insertion
        result1 = await service.persist_jobs([test_job], "indeed")
        assert result1["inserted"] == 1
        assert result1["skipped_duplicates"] == 0
        
        # Second insertion (should be skipped as duplicate)
        result2 = await service.persist_jobs([test_job], "indeed")
        assert result2["inserted"] == 0
        assert result2["skipped_duplicates"] == 1
        
        # Verify _upsert_job was called twice
        assert service._upsert_job.call_count == 2
    
    asyncio.run(run_test())
    print("✅ Idempotency test passed")


def test_batch_processing():
    """Test batch processing with mixed success/error scenarios."""
    print("🧪 Testing batch processing...")
    
    # Create mixed batch: some good, some bad
    jobs = [
        ScrapedJob(title="Good Job 1", job_url="https://example.com/1", site="indeed"),
        ScrapedJob(title="", job_url="https://example.com/2", site="indeed"),  # Bad: no title
        ScrapedJob(title="Good Job 3", job_url="https://example.com/3", site="indeed"),
        ScrapedJob(title="Duplicate", job_url="https://example.com/4", site="indeed"),
    ]
    
    service = JobPersistenceService()
    
    # Mock database 
    mock_conn = AsyncMock()
    service.db_service = Mock()
    service.db_service.initialized = True
    service.db_service.pool = Mock()
    service.db_service.pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    service.db_service.pool.acquire.return_value.__aexit__ = AsyncMock()
    mock_conn.transaction.return_value.__aenter__ = AsyncMock()
    mock_conn.transaction.return_value.__aexit__ = AsyncMock()
    
    # Mock upsert results: inserted, duplicate, inserted (skipping the error case)
    service._upsert_job = AsyncMock(side_effect=["inserted", "duplicate", "inserted"])
    
    async def run_test():
        result = await service.persist_jobs(jobs, "indeed")
        
        # Should have 2 inserts, 1 duplicate, 1 error
        assert result["inserted"] == 2
        assert result["skipped_duplicates"] == 1 
        assert len(result["errors"]) == 1
        assert "missing title" in result["errors"][0]
    
    asyncio.run(run_test())
    print("✅ Batch processing test passed")


def test_convenience_function():
    """Test the convenience persist_jobs function."""
    print("🧪 Testing convenience function...")
    
    # Mock the service
    with patch('app.services.infrastructure.job_persistence.get_job_persistence_service') as mock_get_service:
        mock_service = Mock()
        mock_service.persist_jobs = AsyncMock(return_value={"inserted": 1, "skipped_duplicates": 0, "errors": []})
        mock_get_service.return_value = mock_service
        
        test_jobs = [ScrapedJob(title="Test", job_url="https://example.com/test")]
        
        async def run_test():
            result = await persist_jobs(test_jobs, "indeed")
            assert result["inserted"] == 1
            mock_service.persist_jobs.assert_called_once_with(test_jobs, "indeed")
        
        asyncio.run(run_test())
    
    print("✅ Convenience function test passed")


if __name__ == "__main__":
    print("🧪 Running job persistence tests...\n")
    
    test_job_mapping()
    test_bad_input_handling() 
    test_idempotency()
    test_batch_processing()
    test_convenience_function()
    
    print("\n✅ All job persistence tests passed!")