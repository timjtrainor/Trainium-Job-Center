"""Schemas for LinkedIn job search API endpoints."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LinkedinJobSearchRequest(BaseModel):
    """Request model for LinkedIn job search."""
    job_title: str = Field(
        ..., 
        description="Job title or keywords to search for"
    )
    location: Optional[str] = Field(
        None, 
        description="Geographic location for job search"
    )
    company: Optional[str] = Field(
        None, 
        description="Specific company name to filter by"
    )
    experience_level: Optional[str] = Field(
        None, 
        description="Experience level (entry-level, mid-level, senior, etc.)"
    )
    job_type: Optional[str] = Field(
        None, 
        description="Job type (full-time, part-time, contract, etc.)"
    )
    additional_filters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional search filters and parameters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "Software Engineer",
                "location": "San Francisco, CA",
                "company": "Google",
                "experience_level": "mid-level",
                "job_type": "full-time", 
                "additional_filters": {
                    "remote": True,
                    "salary_min": 120000
                }
            }
        }


class JobSearchResult(BaseModel):
    """Individual job search result."""
    title: str
    company: str
    location: str
    job_type: Optional[str] = None
    description: str
    job_url: str
    date_posted: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_source: Optional[str] = None
    interval: Optional[str] = None
    is_remote: Optional[bool] = None
    company_url: Optional[str] = None
    application_url: Optional[str] = None


class SearchMetadata(BaseModel):
    """Metadata about the job search operation."""
    total_results: int
    search_terms: str
    location_searched: Optional[str] = None
    filters_applied: Optional[str] = None


class ProcessingSummary(BaseModel):
    """Summary of job processing operation."""
    total_processed: int
    validation_errors: List[str] = []
    duplicate_count: int = 0


class LinkedinJobSearchResponse(BaseModel):
    """Response model for LinkedIn job search results."""
    search_results: List[JobSearchResult]
    search_metadata: SearchMetadata
    processing_summary: ProcessingSummary
    persistence_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="Summary of database persistence operation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "search_results": [
                    {
                        "title": "Senior Software Engineer",
                        "company": "Tech Corp",
                        "location": "San Francisco, CA",
                        "job_type": "full-time",
                        "description": "We are looking for a senior software engineer...",
                        "job_url": "https://linkedin.com/jobs/view/123456789",
                        "date_posted": "2024-01-15T10:30:00Z",
                        "salary_min": 150000,
                        "salary_max": 200000,
                        "salary_source": "company",
                        "interval": "yearly",
                        "is_remote": True,
                        "company_url": "https://linkedin.com/company/tech-corp"
                    }
                ],
                "search_metadata": {
                    "total_results": 25,
                    "search_terms": "Software Engineer",
                    "location_searched": "San Francisco, CA",
                    "filters_applied": "full-time, remote-friendly"
                },
                "processing_summary": {
                    "total_processed": 25,
                    "validation_errors": [],
                    "duplicate_count": 2
                },
                "persistence_summary": {
                    "inserted": 23,
                    "skipped_duplicates": 2,
                    "errors": []
                }
            }
        }