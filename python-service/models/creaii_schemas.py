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
    """Complete brand match analysis combining all dimensions (reduced to 5 core dimensions)."""

    # Individual brand dimensions (5 core dimensions)
    north_star: BrandDimensionAnalysis
    trajectory_mastery: BrandDimensionAnalysis
    values_compass: BrandDimensionAnalysis
    lifestyle_alignment: BrandDimensionAnalysis
    compensation_philosophy: BrandDimensionAnalysis

    # Overall synthesis
    overall_alignment_score: float = Field(
        ge=0.0, le=10.0,
        description="Weighted overall score from 5 core dimensions"
    )
    overall_summary: str = Field(
        min_length=20, max_length=1000,
        description="Balanced summary emphasizing compensation, trajectory, and values alignment"
    )
    recommend: bool = Field(description="Final recommendation decision")
    confidence: Literal["low", "medium", "high"] = Field(
        description="Confidence level in the recommendation"
    )


class TldrSummary(BaseModel):
    """Concise TLDR summary of job posting for quick human review."""
    tldr_summary: str = Field(
        description="Brief 3-5 bullet points or paragraph summarizing role, requirements, and seniority"
    )


class BrandDimensionSynthesis(BaseModel):
    """LLM response payload containing dimension analyses and synthesized summary."""

    north_star: BrandDimensionAnalysis
    trajectory_mastery: BrandDimensionAnalysis
    values_compass: BrandDimensionAnalysis
    lifestyle_alignment: BrandDimensionAnalysis
    compensation_philosophy: BrandDimensionAnalysis
    overall_summary: str = Field(
        min_length=20,
        max_length=600,
        description="LLM-generated synthesis that references evidence from each dimension",
    )
    tldr_summary: str = Field(
        min_length=20,
        max_length=400,
        description="Concise human-readable TLDR covering role, requirements, and context",
    )


# Export all models for easy importing
__all__ = [
    "PreFilterResult",
    "BrandDimensionAnalysis",
    "ConstraintsAnalysis",
    "BrandMatchComplete",
    "TldrSummary",
    "BrandDimensionSynthesis",
];
