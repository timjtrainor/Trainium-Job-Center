"""CrewAI service package for scalable multi-crew architecture.

This package provides CrewAI-based services following best practices
for multi-crew systems with YAML-driven configuration.
"""

# Import job review crew first since it doesn't depend on CrewAI library
from .job_review.crew import JobReviewCrew, get_job_review_crew

try:
    from .personal_branding.crew import PersonalBrandCrew, get_personal_brand_crew
    __all__ = [
        "PersonalBrandCrew",
        "get_personal_brand_crew", 
        "JobReviewCrew",
        "get_job_review_crew",
    ]
except ImportError:
    # CrewAI library not available, only export job review
    __all__ = [
        "JobReviewCrew",
        "get_job_review_crew",
    ]

