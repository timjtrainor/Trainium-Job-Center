"""Tests for job persistence service mapping and persistence logic."""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock

from python_service.app.schemas.jobspy import ScrapedJob
from python_service.app.services.infrastructure.job_persistence import JobPersistenceService, persist_jobs


class _DummyTx:
    async def __aenter__(self):
        return None
    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummyConn:
    def transaction(self):
        return _DummyTx()
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummyAcquire:
    def __init__(self, conn):
        self.conn = conn
    async def __aenter__(self):
        return self.conn
    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummyPool:
    def __init__(self):
        self.conn = _DummyConn()
    def acquire(self):
        return _DummyAcquire(self.conn)


def _service(upsert=None):
    service = JobPersistenceService()
    service.db_service = Mock()
    service.db_service.initialized = True
    service.db_service.pool = _DummyPool()
    if upsert is None:
        service._upsert_job = AsyncMock(return_value="inserted")
    else:
        service._upsert_job = AsyncMock(side_effect=upsert)
    return service


def test_job_mapping():
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
        is_remote=True,
    )
    service = _service()
    mapped = service._map_job_to_db(test_job, "indeed")
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
    assert mapped["company_url"] is None
    assert mapped["source_raw"]["title"] == "Senior Python Developer"
    assert mapped["ingested_at"] is not None
    assert mapped["date_posted"] is not None


def test_bad_input_handling():
    bad_jobs = [
        ScrapedJob(title="Python Dev", job_url=""),
        ScrapedJob(title="", job_url="https://example.com/1"),
        ScrapedJob(title="", job_url=""),
        ScrapedJob(title="Good Job", job_url="https://example.com/good"),
    ]
    service = _service()

    async def run_test():
        result = await service.persist_jobs(bad_jobs, "indeed")
        assert result["inserted"] == 1
        assert result["skipped_duplicates"] == 0
        assert len(result["errors"]) == 3
    asyncio.run(run_test())


def test_idempotency():
    test_job = ScrapedJob(
        title="Python Developer",
        job_url="https://example.com/job/duplicate-test",
        company="Test Corp",
        site="indeed",
    )
    service = _service(upsert=["inserted", "duplicate"])

    async def run_test():
        result1 = await service.persist_jobs([test_job], "indeed")
        result2 = await service.persist_jobs([test_job], "indeed")
        assert result1["inserted"] == 1 and result1["skipped_duplicates"] == 0
        assert result2["inserted"] == 0 and result2["skipped_duplicates"] == 1
    asyncio.run(run_test())


def test_batch_processing():
    jobs = [
        ScrapedJob(title="Good Job 1", job_url="https://example.com/1", site="indeed"),
        ScrapedJob(title="", job_url="https://example.com/2", site="indeed"),
        ScrapedJob(title="Good Job 3", job_url="https://example.com/3", site="indeed"),
        ScrapedJob(title="Duplicate", job_url="https://example.com/4", site="indeed"),
    ]
    service = _service(upsert=["inserted", "duplicate", "inserted"])

    async def run_test():
        result = await service.persist_jobs(jobs, "indeed")
        assert result["inserted"] == 2
        assert result["skipped_duplicates"] == 1
        assert len(result["errors"]) == 1
    asyncio.run(run_test())
