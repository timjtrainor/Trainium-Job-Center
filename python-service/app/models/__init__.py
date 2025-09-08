"""
Models package for ORM and business logic models.

This package contains Pydantic models used throughout the application
for data validation, serialization, and business logic.
"""
from .job_posting import JobPosting
from .fit_review import (
    PersonaVerdict,
    FitReviewResult,
    JudgeDecision,
    ConfidenceLevel,
    FinalRecommendation,
)

__all__ = [
    "JobPosting",
    "PersonaVerdict", 
    "FitReviewResult",
    "JudgeDecision",
    "ConfidenceLevel",
    "FinalRecommendation",
]
