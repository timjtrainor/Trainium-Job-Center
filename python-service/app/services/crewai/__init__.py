"""CrewAI service package for scalable multi-crew architecture.

This package provides CrewAI-based services following best practices
for multi-crew systems with YAML-driven configuration.
"""

from .job_review.crew import JobReviewCrew, get_job_review_crew
from .personal_branding.crew import PersonalBrandCrew, get_personal_brand_crew
from .research_company.crew import ResearchCompanyCrew, get_research_company_crew
from .job_posting_review.crew import JobPostingReviewCrew, get_job_posting_review_crew

__all__ = [
    "JobReviewCrew",
    "get_job_review_crew",
    "PersonalBrandCrew",
    "get_personal_brand_crew",
    "ResearchCompanyCrew",
    "get_research_company_crew",
    "JobPostingReviewCrew",
    "get_job_posting_review_crew",
]

