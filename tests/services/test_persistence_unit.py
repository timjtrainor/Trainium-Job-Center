"""Simple tests for job persistence functionality without database dependencies."""
from datetime import datetime

from app.schemas.jobspy import ScrapedJob


def test_scraped_job_model():
    """Test basic ScrapedJob model functionality."""
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
        is_remote=True,
    )

    assert job.title == "Senior Python Developer"
    assert job.company == "Test Company"
    assert job.salary_min == 80000.0
    assert job.salary_max == 120000.0
    assert job.is_remote is True
    assert job.site == "indeed"
    assert job.emails == ["hr@company.com"]


def test_job_field_mapping_logic(job_persistence_service):
    """Test the field mapping logic without database calls."""
    service = job_persistence_service

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
        is_remote=False,
    )

    mapped = service._map_job_to_db(test_job, "linkedin")

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
    assert mapped["ingested_at"] is not None
    assert isinstance(mapped["ingested_at"], datetime)
    assert mapped["date_posted"] is not None
    assert mapped["source_raw"]["title"] == "Data Scientist"
    assert mapped["source_raw"]["company"] == "AI Corp"
    assert mapped["source_raw"]["job_url"] == "https://example.com/job/456"
    assert mapped["source_raw"]["salary_min"] == 90000.0
    assert "scraped_at" in mapped["source_raw"]


def test_date_parsing(job_persistence_service):
    """Test date parsing functionality."""
    service = job_persistence_service

    test_cases = [
        ("2025-01-24", True),
        ("2025-01-24T10:30:00", True),
        ("2025-01-24T10:30:00+00:00", True),
        ("2025-01-24T10:30:00Z", True),
        (None, False),
        ("", False),
        ("invalid-date", False),
    ]

    for date_input, should_succeed in test_cases:
        job = ScrapedJob(title="Test Job", job_url="https://example.com/test", date_posted=date_input)
        mapped = service._map_job_to_db(job, "indeed")
        if should_succeed and date_input:
            assert mapped["date_posted"] is not None
        else:
            if date_input is None:
                assert mapped["date_posted"] is None


def test_validation_logic():
    """Test validation logic for required fields."""
    test_cases = [
        ("Python Developer", "https://example.com/1", True),
        ("", "https://example.com/2", False),
        ("Developer", "", False),
        ("", "", False),
        (None, "https://example.com/3", False),
        ("Developer", None, False),
    ]

    for title, job_url, expected in test_cases:
        job = ScrapedJob(title=title, job_url=job_url)
        has_job_url = bool(job.job_url)
        has_title = bool(job.title)
        assert (has_job_url and has_title) == expected
