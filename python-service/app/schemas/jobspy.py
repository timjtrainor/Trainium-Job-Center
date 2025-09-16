"""
JobSpy integration schemas for job scraping and ingestion.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
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
    """Request model for job scraping with enhanced pagination support."""
    site_name: JobSite = Field(default=JobSite.INDEED, description="Job site to scrape from")
    search_term: Optional[str] = Field(..., description="Job search term/keywords")
    location: Optional[str] = Field(default=None, description="Job location")
    is_remote: bool = Field(default=False, description="Search for remote jobs only")
    job_type: Optional[JobType] = Field(default=None, description="Job type filter")
    results_wanted: int = Field(default=15, ge=1, le=500, description="Number of results to return (with pagination: up to 500)")
    distance: Optional[int] = Field(default=50, description="Search radius in miles")
    easy_apply: Optional[bool] = Field(default=None, description="Filter for easy apply jobs")
    hours_old: Optional[int] = Field(default=None, description="Filter jobs posted within X hours")
    
    # Pagination enhancement fields
    enable_pagination: bool = Field(default=False, description="Enable pagination workarounds for >25 results")
    max_results_target: Optional[int] = Field(default=None, description="Target result count when pagination enabled")
    
    # Site-specific
    google_search_term: Optional[str] = Field(default=None, description="Google search term only used for Google Job Board")
    country_indeed: Optional[str] = Field(default="USA", description="Required for Indeed/Glassdoor and is the country USA")
    linkedin_fetch_description: Optional[bool] = Field(default=None, description="For LinkedIn gets more info such as description, direct job url (SLOWER)")  # LinkedIn
    linkedin_company_ids: Optional[List[int]] = Field(default=None, description="List of LinkedIn company IDs to filter by")  # LinkedIn

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

    @field_validator("emails", mode="before")
    @classmethod
    def _wrap_emails(cls, value):
        if value is None or isinstance(value, list):
            return value
        return [value]


class JobSearchResponse(BaseModel):
    """Response model for job scraping results."""
    total_found: int = Field(description="Total number of jobs found")
    jobs: List[ScrapedJob] = Field(description="List of scraped jobs")
    search_metadata: dict = Field(description="Search parameters and metadata")
