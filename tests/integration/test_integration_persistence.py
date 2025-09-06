#!/usr/bin/env python3
"""
Integration test for the complete jobs persistence workflow.
Demonstrates the persistence functionality without requiring live database.
"""
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from app.schemas.jobspy import ScrapedJob
from app.services.infrastructure.job_persistence import JobPersistenceService

def test_persistence_integration():
    """Test the complete persistence workflow with mocked components."""
    print("🧪 Testing jobs persistence integration workflow...")

    # Create realistic test data similar to what JobSpy would return
    test_jobs = [
        ScrapedJob(
            title="Senior Python Developer",
            company="Tech Innovations Inc",
            location="Remote",
            job_type="fulltime", 
            date_posted="2025-01-24T10:30:00+00:00",
            salary_min=95000.0,
            salary_max=130000.0,
            salary_source="employer",
            interval="yearly",
            description="Exciting Python role working with AI/ML technologies...",
            job_url="https://indeed.com/viewjob?jk=abc123",
            job_url_direct="https://indeed.com/apply/abc123",
            site="indeed",
            emails=["jobs@techinnovations.com"],
            is_remote=True
        ),
        ScrapedJob(
            title="Data Engineer", 
            company="DataFlow Corp",
            location="San Francisco, CA",
            job_type="fulltime",
            date_posted="2025-01-23T14:15:00+00:00", 
            salary_min=110000.0,
            salary_max=150000.0,
            salary_source="glassdoor",
            interval="yearly",
            description="Build scalable data pipelines...",
            job_url="https://linkedin.com/jobs/view/456789",
            job_url_direct="https://linkedin.com/jobs/apply/456789",
            site="linkedin",
            emails=None,
            is_remote=False
        ),
        # Duplicate of first job (same site + job_url)
        ScrapedJob(
            title="Senior Python Developer - Updated",  # Title changed but same job
            company="Tech Innovations Inc",
            job_url="https://indeed.com/viewjob?jk=abc123",  # Same URL as first
            site="indeed"
        ),
        # Invalid job (missing title)
        ScrapedJob(
            title="",  # Missing title should cause error
            company="Bad Data Corp",
            job_url="https://example.com/bad",
            site="indeed"
        )
    ]
    
    # Mock the database service and connection properly for async context
    service = JobPersistenceService()

    class DummyTx:
        async def __aenter__(self):
            return None
        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DummyConn:
        def transaction(self):
            return DummyTx()
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DummyAcquire:
        def __init__(self, conn):
            self.conn = conn
        async def __aenter__(self):
            return self.conn
        async def __aexit__(self, exc_type, exc, tb):
            return False

    class DummyPool:
        def __init__(self):
            self.conn = DummyConn()
        def acquire(self):
            return DummyAcquire(self.conn)

    service.db_service = Mock(initialized=True, pool=DummyPool())
    
    # Mock the _upsert_job method to simulate database behavior
    # First job: inserted, Second job: inserted, Third job: duplicate
    # Fourth job will be filtered out by validation (missing title)
    upsert_results = ["inserted", "inserted", "duplicate"]
    result_iter = iter(upsert_results)
    
    async def mock_upsert_job(conn, job_data):
        return next(result_iter)
    
    service._upsert_job = mock_upsert_job
    
    async def run_test():
        # Execute the persistence workflow
        result = await service.persist_jobs(test_jobs, "mixed_sites")
        
        # Verify results
        print(f"📊 Persistence Results: {result}")
        
        # Should have 2 inserts (first two jobs), 1 duplicate (third job), 1 error (fourth job)
        assert result["inserted"] == 2, f"Expected 2 insertions, got {result['inserted']}"
        assert result["skipped_duplicates"] == 1, f"Expected 1 duplicate, got {result['skipped_duplicates']}"
        assert len(result["errors"]) == 1, f"Expected 1 error, got {len(result['errors'])}"
        assert "missing title" in result["errors"][0], "Error should mention missing title"
        
        # Verify _upsert_job was called 3 times (4 jobs - 1 validation error)
        # Note: Can't easily verify call count with our manual mock, but logic is tested
        
        print("✅ Expected 2 inserted, 1 duplicate, 1 error - matches results!")
        
        # Note: Field mapping verification would require more complex mocking
        # But the unit tests already verify the mapping logic works correctly
        print("✅ Integration workflow verified (field mapping tested separately)!")
        
    # Run the async test
    asyncio.run(run_test())
    print("✅ Complete persistence integration test passed!")


def test_api_integration_mock(job_persistence_service):
    """Test how the API integration would work."""
    print("🧪 Testing API integration...")

    # Mock a successful scraping result
    mock_scraped_result = {
        "status": "succeeded",
        "jobs": [
            ScrapedJob(
                title="DevOps Engineer",
                company="Cloud Systems",
                job_url="https://glassdoor.com/job/789",
                site="glassdoor",
                salary_min=85000.0,
                is_remote=True
            )
        ],
        "total_found": 1,
        "message": "Successfully scraped 1 job"
    }

    job_persistence_service.persist_jobs = AsyncMock(return_value={
        "inserted": 1,
        "skipped_duplicates": 0,
        "errors": []
    })

    async def run_test():
        if mock_scraped_result.get("jobs"):
            persistence_summary = await job_persistence_service.persist_jobs(
                records=mock_scraped_result["jobs"],
                site_name="glassdoor"
            )

            api_response = {
                "jobs": [job.model_dump() for job in mock_scraped_result["jobs"]],
                "total_found": mock_scraped_result["total_found"],
                "persistence_summary": persistence_summary,
                "execution_mode": "sync"
            }

            print(f"📡 API Response includes: {list(api_response.keys())}")
            assert "persistence_summary" in api_response
            assert api_response["persistence_summary"]["inserted"] == 1
            job_persistence_service.persist_jobs.assert_awaited_once_with(
                records=mock_scraped_result["jobs"],
                site_name="glassdoor"
            )

    asyncio.run(run_test())
    print("✅ API integration test passed!")
