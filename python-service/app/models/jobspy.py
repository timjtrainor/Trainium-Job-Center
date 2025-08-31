"""
JobSpy integration models for job scraping and ingestion.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class JobSite(str, Enum):
    """Supported job sites for scraping."""
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    ZIPRECRUITER = "ziprecruiter"
    GOOGLE = "google"


class JobType(str, Enum):
    """Job type filter options."""
    FULL_TIME = "fulltime"
    PART_TIME = "parttime"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"


class JobSearchRequest(BaseModel):
    """Request model for job scraping."""
    site_name: JobSite = Field(default=JobSite.INDEED, description="Job site to scrape from")
    search_term: str = Field(..., description="Job search term/keywords")
    location: Optional[str] = Field(default=None, description="Job location")
    is_remote: bool = Field(default=False, description="Search for remote jobs only")
    job_type: Optional[JobType] = Field(default=None, description="Job type filter")
    results_wanted: int = Field(default=15, ge=1, le=100, description="Number of results to return")
    distance: Optional[int] = Field(default=50, description="Search radius in miles")
    easy_apply: Optional[bool] = Field(default=None, description="Filter for easy apply jobs")
    hours_old: Optional[int] = Field(default=None, description="Filter jobs posted within X hours")


class ScrapedJob(BaseModel):
    """Model for individual scraped job data."""
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    date_posted: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_source: Optional[str] = None
    interval: Optional[str] = None
    description: Optional[str] = None
    job_url: Optional[str] = None
    job_url_direct: Optional[str] = None
    site: Optional[str] = None
    emails: Optional[List[str]] = None
    is_remote: Optional[bool] = None


class JobSearchResponse(BaseModel):
    """Response model for job scraping results."""
    total_found: int = Field(description="Total number of jobs found")
    jobs: List[ScrapedJob] = Field(description="List of scraped jobs")
    search_metadata: dict = Field(description="Search parameters and metadata")