"""LinkedIn Recommended Jobs CrewAI implementation.

This crew is responsible for fetching job postings from LinkedIn and normalizing
them into the JobPosting schema. It does not perform any recommendation logic,
filtering, ranking, or evaluation of job fit.

Key Functions:
- Fetch personalized job recommendations using MCP LinkedIn tools
- Retrieve detailed job posting information
- Normalize output to JobPosting schema
- Update project documentation
"""

from .crew import (
    LinkedInRecommendedJobsCrew,
    get_linkedin_recommended_jobs_crew,
    run_linkedin_recommended_jobs,
)

__all__ = [
    "LinkedInRecommendedJobsCrew",
    "get_linkedin_recommended_jobs_crew",
    "run_linkedin_recommended_jobs",
]
