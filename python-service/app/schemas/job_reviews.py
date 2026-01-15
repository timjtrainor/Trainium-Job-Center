"""Schema for job reviews endpoints."""
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal


class JobReviewData(BaseModel):
    """Schema for job review details."""
    overall_alignment_score: Optional[float] = Field(None, description="Overall alignment score from review")
    recommendation: bool = Field(..., description="Final recommendation: true=recommend, false=do not recommend")
    confidence: str = Field(..., description="Confidence level returned by the CrewAI workflow")
    reviewer: Optional[str] = Field(None, description="Model or crew version used for review")
    review_date: datetime = Field(..., description="When the review was created")
    rationale: Optional[str] = Field(None, description="Human-readable explanation of the recommendation")
    personas: Optional[List[Dict[str, Any]]] = Field(None, description="Individual persona evaluations")
    tradeoffs: Optional[List[Any]] = Field(None, description="Trade-off analysis")
    actions: Optional[List[Any]] = Field(None, description="Recommended actions")
    sources: Optional[Union[List[Any], Dict[str, Any]]] = Field(None, description="Information sources used")
    tldr_summary: Optional[str] = Field(None, description="Concise 10-20 second TLDR summary for quick human review")
    crew_output: Optional[Dict[str, Any]] = Field(None, description="Raw CrewAI agent output including dimension scores")
    override_recommend: Optional[bool] = Field(None, description="Human override of AI recommendation")
    override_comment: Optional[str] = Field(None, description="Human reviewer comment explaining the override decision")
    override_by: Optional[str] = Field(None, description="Identifier of the human reviewer who made the override")
    override_at: Optional[datetime] = Field(None, description="Timestamp when the human override was made")


class JobDetails(BaseModel):
    """Schema for job posting details."""
    job_id: str = Field(..., description="Unique job identifier")
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    location: Optional[str] = Field(None, description="Job location")
    url: Optional[str] = Field(None, description="Job posting URL")
    date_posted: Optional[datetime] = Field(None, description="When job was originally posted")
    source: Optional[str] = Field(None, description="Job board source (indeed, linkedin, etc.)")
    description: Optional[str] = Field(None, description="Job description")
    salary_min: Optional[Decimal] = Field(None, description="Minimum salary amount")
    salary_max: Optional[Decimal] = Field(None, description="Maximum salary amount")
    salary_currency: Optional[str] = Field(None, description="Salary currency")
    salary_range: Optional[str] = Field(None, description="Formatted salary range for display")
    is_remote: Optional[bool] = Field(None, description="Remote work flag")
    normalized_title: Optional[str] = Field(None, description="Normalized job title for competency tracking")
    normalized_company: Optional[str] = Field(None, description="Normalized company name")
    track: Optional[str] = Field(None, description="Job track for competency identification")


class ReviewedJob(BaseModel):
    """Schema for combined job + review data."""
    job: JobDetails = Field(..., description="Job posting details")
    review: JobReviewData = Field(..., description="Review details")


class ReviewedJobsResponse(BaseModel):
    """Response model for reviewed jobs endpoint."""
    jobs: List[ReviewedJob] = Field(..., description="List of reviewed jobs")
    total_count: int = Field(..., description="Total number of reviewed jobs matching filters")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_more: bool = Field(..., description="Whether there are more pages available")


class ReviewedJobsFilters(BaseModel):
    """Query filters for reviewed jobs endpoint."""
    recommendation: Optional[bool] = Field(None, description="Filter by recommendation status")
    min_score: Optional[float] = Field(None, description="Minimum alignment score", ge=0.0, le=1.0)
    max_score: Optional[float] = Field(None, description="Maximum alignment score", ge=0.0, le=1.0)
    company: Optional[str] = Field(None, description="Filter by company name (partial match)")
    source: Optional[str] = Field(None, description="Filter by job source")
    is_remote: Optional[bool] = Field(None, description="Filter by remote work availability")
    date_posted_after: Optional[datetime] = Field(None, description="Filter jobs posted after this date")
    date_posted_before: Optional[datetime] = Field(None, description="Filter jobs posted before this date")
