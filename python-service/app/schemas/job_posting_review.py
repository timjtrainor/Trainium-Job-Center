from typing import Any, Dict, Optional

from pydantic import BaseModel


class JobPostingReviewOutput(BaseModel):
    """Model for orchestrated job posting review output."""

    job_intake: Dict[str, Any]
    pre_filter: Dict[str, Any]
    quick_fit: Optional[Dict[str, Any]] = None
    brand_match: Optional[Dict[str, Any]] = None
