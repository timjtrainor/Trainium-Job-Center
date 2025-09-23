"""Schemas for LinkedIn recommended jobs API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
