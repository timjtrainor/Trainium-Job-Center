"""Schemas for the LinkedIn recommended jobs FastAPI endpoint."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LinkedInRecommendedJobSummary(BaseModel):
    """Summary information for a LinkedIn recommended job."""

    job_id: str = Field(..., description="LinkedIn job identifier")
    job_title: Optional[str] = Field(default=None, description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    location: Optional[str] = Field(default=None, description="Job location")
    match_reason: Optional[str] = Field(default=None, description="Why this job was recommended")
    job_url: Optional[str] = Field(default=None, description="LinkedIn job URL")


class LinkedInEnrichedJobDetail(BaseModel):
    """Detailed LinkedIn job insight produced by the enrichment task."""

    job_id: str = Field(..., description="LinkedIn job identifier")
    job_title: Optional[str] = Field(default=None, description="Job title")
    company: Optional[str] = Field(default=None, description="Company name")
    location: Optional[str] = Field(default=None, description="Job location")
    job_description: Optional[str] = Field(default=None, description="Full job description text")
    key_requirements: Optional[List[str]] = Field(default=None, description="Key qualifications or requirements")
    company_insights: Optional[List[str]] = Field(default=None, description="Insights about the hiring company")
    next_steps: Optional[List[str]] = Field(default=None, description="Suggested candidate actions")
    match_reason: Optional[str] = Field(default=None, description="Why this job aligns with the candidate")
    job_url: Optional[str] = Field(default=None, description="LinkedIn job URL")


class LinkedInRecommendedJobsResult(BaseModel):
    """Payload returned by the LinkedIn recommended jobs endpoint."""

    request_id: str = Field(..., description="Correlation identifier for the request")
    discovered_jobs: List[LinkedInRecommendedJobSummary] = Field(
        default_factory=list,
        description="List of discovered LinkedIn recommendations",
    )
    enriched_jobs: List[LinkedInEnrichedJobDetail] = Field(
        default_factory=list,
        description="List of enriched LinkedIn job details",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata from the crew run")


__all__ = [
    "LinkedInRecommendedJobSummary",
    "LinkedInEnrichedJobDetail",
    "LinkedInRecommendedJobsResult",
]
