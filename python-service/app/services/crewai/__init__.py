"""
CrewAI service package for scalable multi-crew architecture.

This package provides CrewAI-based services following best practices
for multi-crew systems with YAML-driven configuration.
"""
from .job_review.crew import JobReviewCrew, get_job_review_crew

__all__ = [
    "JobReviewCrew",
    "get_job_review_crew",
]