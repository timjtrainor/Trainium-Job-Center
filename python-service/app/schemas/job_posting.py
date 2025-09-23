"""JobPosting schema definitions for LinkedIn recommended jobs."""

# Defensive imports with graceful fallback
try:
    from pydantic import BaseModel, Field, HttpUrl
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Create fallback classes for when Pydantic is not available
    class BaseModel:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
        
        def dict(self):
            return self.__dict__
    
    def Field(**kwargs):
        return None
    
    # Simple URL type for fallback
    HttpUrl = str

from typing import List, Dict, Any, Optional


class JobPosting(BaseModel):
    """Standard JobPosting schema for LinkedIn job data."""
    
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Full job description")
    url: HttpUrl = Field(..., description="URL to the job posting")


class LinkedInRecommendedJobsResponse(BaseModel):
    """Response model for LinkedIn recommended jobs endpoint."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    job_postings: List[JobPosting] = Field(default_factory=list, description="List of job postings")
    total_count: int = Field(0, description="Total number of job postings retrieved")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    error_message: Optional[str] = Field(None, description="Error message if operation failed")


class LinkedInRecommendedJobsRequest(BaseModel):
    """Request model for LinkedIn recommended jobs endpoint."""
    
    # No input parameters needed - fetches recommendations for current logged-in user
    pass