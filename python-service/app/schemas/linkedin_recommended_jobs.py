"""Schemas for LinkedIn recommended jobs API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class LinkedInRecommendedJobsRequest(BaseModel):
    """Request payload for generating LinkedIn recommended jobs."""

    user_id: str = Field(..., description="Identifier for the user requesting recommendations.")
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of recommended roles to return.",
    )
    profile_url: Optional[HttpUrl] = Field(
        default=None,
        description="Optional LinkedIn profile URL that can be supplied explicitly by the caller.",
    )
    job_preferences: Optional[List[str]] = Field(
        default=None,
        description="List of job preference keywords to emphasize during recommendation analysis.",
    )
    target_companies: Optional[List[str]] = Field(
        default=None,
        description="Companies the user is especially interested in pursuing.",
    )
    location_preferences: Optional[List[str]] = Field(
        default=None,
        description="Preferred locations or geographic filters for recommended jobs.",
    )
    include_remote: Optional[bool] = Field(
        default=None,
        description="Whether to prioritize remote-friendly opportunities.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes or context that should be considered by the crew.",
    )


class LinkedInRecommendedJobsResponse(BaseModel):
    """Response payload returned from the LinkedIn recommended jobs crew."""

    success: bool = Field(default=True, description="Indicates whether the crew run succeeded.")
    recommended_jobs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Collection of recommended job dictionaries produced by the crew.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supplemental metadata describing how the recommendations were produced.",
    )
    summary: Optional[str] = Field(
        default=None,
        description="Optional narrative summary or insight report accompanying the recommendations.",
    )
