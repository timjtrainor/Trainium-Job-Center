from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobPostingReviewOutput(BaseModel):
    """Model for orchestrated job posting review output."""

    job_intake: Dict[str, Any]
    pre_filter: Dict[str, Any]
    quick_fit: Optional[Dict[str, Any]] = None
    brand_match: Optional[Dict[str, Any]] = None
    final: Dict[str, Any]
    personas: List[Dict[str, Any]] = Field(default_factory=list)
    tradeoffs: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
