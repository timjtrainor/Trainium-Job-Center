"""
Pydantic models for CrewAI task output validation.
Ensures all agents return properly structured JSON.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class PreFilterResult(BaseModel):
    """Pre-filter agent output validation."""
    recommend: bool = Field(description="Whether the job should proceed to detailed analysis")
    reason: Optional[str] = Field(
        default=None,
        description="Reason for rejection, required if recommend=False"
    )


class BrandDimensionAnalysis(BaseModel):
    """Individual brand dimension analysis output validation."""
    score: int = Field(
        ge=1, le=5,
        description="Tier score: 1=critical mismatch, 5=exceptional fit"
    )
    summary: str = Field(
        min_length=10, max_length=500,
        description="Detailed assessment with specific reasons from career brand data"
    )


class ConstraintsAnalysis(BrandDimensionAnalysis):
    """Constraints analysis with deal-breakers."""
    constraint_issues: str = Field(
        default="none",
        description="Specific deal-breakers violated or 'none' if compliant"
    )


class BrandMatchComplete(BaseModel):
    """Complete brand match analysis combining all dimensions."""

    # Individual brand dimensions
    north_star: BrandDimensionAnalysis
    trajectory_mastery: BrandDimensionAnalysis
    values_compass: BrandDimensionAnalysis
    lifestyle_alignment: BrandDimensionAnalysis
    compensation_philosophy: BrandDimensionAnalysis
    purpose_impact: BrandDimensionAnalysis
    industry_focus: BrandDimensionAnalysis
    company_filters: BrandDimensionAnalysis
    constraints: ConstraintsAnalysis

    # Overall synthesis
    overall_alignment_score: float = Field(
        ge=0.0, le=10.0,
        description="Weighted overall score from individual dimensions"
    )
    overall_summary: str = Field(
        min_length=20, max_length=1000,
        description="Balanced summary emphasizing constraints, compensation, and trajectory"
    )
    recommend: bool = Field(description="Final recommendation decision")
    confidence: Literal["low", "medium", "high"] = Field(
        description="Confidence level in the recommendation"
    )
    constraint_issues: str = Field(
        default="none",
        description="Any critical constraints that override other factors"
    )


# Export all models for easy importing
__all__ = [
    "PreFilterResult",
    "BrandDimensionAnalysis",
    "ConstraintsAnalysis",
    "BrandMatchComplete",
];
