"""
Schemas for LinkedIn Job Search CrewAI integration.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .jobspy import ScrapedJob


class LinkedInJobSearchRequest(BaseModel):
    """Request model for LinkedIn job search parameters."""
    keywords: str = Field(..., description="Job search keywords")
    location: Optional[str] = Field(default=None, description="Job location")
    job_type: Optional[str] = Field(default=None, description="Job type filter (full-time, part-time, contract, etc.)")
    date_posted: Optional[str] = Field(default=None, description="Date filter (past-24h, past-week, past-month)")
    experience_level: Optional[str] = Field(default=None, description="Experience level (entry, mid, senior)")
    remote: bool = Field(default=False, description="Search for remote jobs only")
    limit: int = Field(default=25, ge=1, le=100, description="Maximum number of results")


class LinkedInJobSearchResponse(BaseModel):
    """Response model for LinkedIn job search results."""
    success: bool = Field(description="Whether the search was successful")
    consolidated_jobs: List[ScrapedJob] = Field(description="List of consolidated job results")
    total_jobs: int = Field(description="Total number of jobs after deduplication")
    search_jobs_count: int = Field(default=0, description="Number of jobs from search")
    recommended_jobs_count: int = Field(default=0, description="Number of jobs from recommendations")
    duplicates_removed: int = Field(default=0, description="Number of duplicate jobs removed")
    consolidation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Search execution metadata")
    error: Optional[str] = Field(default=None, description="Error message if search failed")


class LinkedInJobSearchStatus(BaseModel):
    """Status model for LinkedIn job search operations."""
    search_success: bool = Field(description="Whether job search succeeded")
    recommendations_success: bool = Field(description="Whether recommendations retrieval succeeded") 
    authentication_status: str = Field(description="LinkedIn authentication status")
    total_operations: int = Field(description="Total number of operations attempted")
    successful_operations: int = Field(description="Number of successful operations")
    errors: List[str] = Field(default_factory=list, description="List of any errors encountered")