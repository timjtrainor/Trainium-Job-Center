"""CrewAI service package for scalable multi-crew architecture."""

from .linkedin_job_search.crew import (
    LinkedInJobSearchCrew,
    get_linkedin_job_search_crew,
)
from .linkedin_recommended_jobs.crew import (
    LinkedInRecommendedJobsCrew,
    get_linkedin_recommended_jobs_crew,
)
from .personal_branding.crew import (
    PersonalBrandCrew,
    get_personal_brand_crew,
)
from .research_company.crew import (
    ResearchCompanyCrew,
    get_research_company_crew,
)

__all__ = [
    "PersonalBrandCrew",
    "get_personal_brand_crew",
    "ResearchCompanyCrew",
    "get_research_company_crew",
    "LinkedInJobSearchCrew",
    "get_linkedin_job_search_crew",
    "LinkedInRecommendedJobsCrew",
    "get_linkedin_recommended_jobs_crew",
]
