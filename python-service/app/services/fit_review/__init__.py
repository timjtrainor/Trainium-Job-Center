"""
Fit Review service package.

This package implements the CrewAI-powered job posting fit review pipeline,
including orchestration, judgment, retrieval, and persona helper agents.
"""
# from .orchestrator import FitReviewOrchestrator
from .judge import FitReviewJudge
from .retrieval import normalize_jd, get_career_brand_digest, build_context

__all__ = [
    # "FitReviewOrchestrator",
    "FitReviewJudge", 
    "normalize_jd",
    "get_career_brand_digest", 
    "build_context",
]