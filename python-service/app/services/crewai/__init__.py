"""CrewAI service package for scalable multi-crew architecture.

This package provides CrewAI-based services following best practices
for multi-crew systems with YAML-driven configuration.
"""

from .personal_branding.crew import PersonalBrandCrew, get_personal_brand_crew
from .research_company.crew import ResearchCompanyCrew, get_research_company_crew
from .linkedin_job_search.crew import LinkedInJobSearchCrew, get_linkedin_job_search_crew

__all__ = [
    "PersonalBrandCrew",
    "get_personal_brand_crew",
    "ResearchCompanyCrew", 
    "get_research_company_crew",
    "LinkedInJobSearchCrew",
    "get_linkedin_job_search_crew",
]

