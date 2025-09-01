"""
JobSpy ingestion service for scraping jobs from various job boards.
Integrates with the python-jobspy library to fetch job postings.
"""
from typing import Optional, List, Dict, Any
import asyncio
from datetime import date, datetime
import pandas as pd
from loguru import logger

from jobspy import scrape_jobs
from ..core.config import get_settings
from ..models.responses import StandardResponse, create_success_response, create_error_response
from ..models.jobspy import JobSearchRequest, JobSearchResponse, ScrapedJob
def _to_iso_date_str(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    # pandas.NaT handling
    if pd.isna(value):
        return None
    # pandas.Timestamp -> datetime
    if isinstance(value, pd.Timestamp):
        # prefer date-only ISO if no time component
        if value.hour == 0 and value.minute == 0 and value.second == 0 and value.tz is None:
            return value.date().isoformat()
        return value.to_pydatetime().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    # already a string
    return str(value)

def _to_optional_list(value):
    # JobSpy sometimes returns emails as list, stringified list, or NaN
    if value is None or pd.isna(value):
        return None
    if isinstance(value, list):
        return value or None
    # try to parse stringified list
    try:
        import ast
        parsed = ast.literal_eval(value) if isinstance(value, str) else value
        return parsed if isinstance(parsed, list) and parsed else None
    except Exception:
        return [str(value)]
# --- end helpers ---

class JobSpyIngestionService:
    """
    Service class for handling job scraping via JobSpy integration.
    Provides methods to scrape jobs from various job boards and format them
    for integration with the Trainium Job Center application.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize the JobSpy ingestion service.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # JobSpy doesn't require specific initialization, just mark as ready
            self.initialized = True
            logger.info("JobSpy ingestion service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize JobSpy ingestion service: {str(e)}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the JobSpy ingestion service.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        return {
            "service": "jobspy_ingestion",
            "initialized": self.initialized,
            "supported_sites": ["indeed", "linkedin", "glassdoor", "ziprecruiter", "google"],
            "status": "ready" if self.initialized else "not_initialized"
        }
    
    async def scrape_jobs_async(self, request: JobSearchRequest) -> StandardResponse:
        """
        Scrape jobs asynchronously using JobSpy.
        
        Args:
            request: JobSearchRequest with search parameters
            
        Returns:
            StandardResponse containing scraped job data
        """
        try:
            if not self.initialized:
                await self.initialize()
            
            logger.info(f"Starting job scrape: {request.search_term} on {request.site_name}")
            
            # Run the potentially blocking JobSpy operation in a thread pool
            # add to imports if not already present
            from typing import Optional

            # ... inside JobSpyIngestionService.scrape_jobs_async(...)
            def _scrape_sync():
                # Base kwargs used everywhere
                kwargs = {
                    "site_name": request.site_name.value,
                    "results_wanted": request.results_wanted,
                    "description_format": "markdown",
                    "verbose": 1,
                }

                site = request.site_name.value

                if site == "google":
                    # Google: only google_search_term is honored
                    google_q = request.google_search_term
                    if not google_q:
                        # Fallback: synthesize a decent Google query
                        parts = []
                        if request.search_term:
                            parts.append(request.search_term)
                        if request.location:
                            parts.append(f"jobs near {request.location}")
                        if request.hours_old:
                            parts.append(f"posted last {int(request.hours_old)} hours")
                        google_q = " ".join(parts).strip() or "software engineer jobs"
                    kwargs["google_search_term"] = google_q
                    # Do NOT pass job_type, easy_apply, is_remote, distance, etc. for Google.  # docs say google_search_term is the only filter
                    # https://github.com/speedyapply/JobSpy README
                else:
                    # Non-Google use structured filters selectively
                    if request.search_term:
                        kwargs["search_term"] = request.search_term
                    if request.location:
                        kwargs["location"] = request.location
                    if request.is_remote is not None:
                        kwargs["is_remote"] = request.is_remote
                    if request.job_type:
                        kwargs["job_type"] = request.job_type.value
                    if request.distance:
                        kwargs["distance"] = request.distance
                    if request.hours_old:
                        kwargs["hours_old"] = request.hours_old

                    # Board-specific toggles and constraints
                    if site in {"indeed", "glassdoor"}:
                        # country_indeed is required to target country on these sites
                        country = request.country_indeed or getattr(self.settings, "country_indeed", None)
                        if country:
                            kwargs["country_indeed"] = country
                        # Indeed limitation: only one of {hours_old} OR {job_type/is_remote} OR {easy_apply}
                        # If easy_apply is set, prefer it and drop the others per docs.
                        if request.easy_apply is not None:
                            kwargs["easy_apply"] = request.easy_apply
                            # enforce “only one” by removing conflicting keys
                            kwargs.pop("hours_old", None)
                            kwargs.pop("job_type", None)
                            kwargs.pop("is_remote", None)
                    elif site == "linkedin":
                        if request.linkedin_fetch_description is not None:
                            kwargs["linkedin_fetch_description"] = request.linkedin_fetch_description
                        if request.linkedin_company_ids:
                            kwargs["linkedin_company_ids"] = request.linkedin_company_ids
                        # LinkedIn limitation: only one of {hours_old} OR {easy_apply}
                        if request.easy_apply is not None:
                            kwargs["easy_apply"] = request.easy_apply
                            kwargs.pop("hours_old", None)
                    elif site == "zip_recruiter":
                        # no special params beyond the general ones; note hours_old rounds to next day upstream
                        pass

                return scrape_jobs(**kwargs)
            
            # Run in thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            jobs_df = await loop.run_in_executor(None, _scrape_sync)
            
            # Convert pandas DataFrame to our response format
            jobs_list = []
            if not jobs_df.empty:
                for _, row in jobs_df.iterrows():
                    job = ScrapedJob(
                        title=row.get("title"),
                        company=row.get("company"),
                        location=row.get("location"),
                        job_type=(row.get("job_type") if pd.notna(row.get("job_type")) else None),
                        date_posted=_to_iso_date_str(row.get("date_posted")),  # <-- normalize here
                        salary_min=(row.get("min_amount") if pd.notna(row.get("min_amount")) else None),
                        salary_max=(row.get("max_amount") if pd.notna(row.get("max_amount")) else None),
                        salary_source=(row.get("salary_source") if pd.notna(row.get("salary_source")) else None),
                        interval=(row.get("interval") if pd.notna(row.get("interval")) else None),
                        description=row.get("description"),
                        job_url=row.get("job_url"),
                        job_url_direct=row.get("job_url_direct"),
                        site=row.get("site"),
                        emails=_to_optional_list(row.get("emails")),
                        is_remote=bool(row.get("is_remote")) if not pd.isna(row.get("is_remote")) else None,
                    )
                    jobs_list.append(job)
            
            response_data = JobSearchResponse(
                total_found=len(jobs_list),
                jobs=jobs_list,
                search_metadata={
                    "site": request.site_name.value,
                    "search_term": request.search_term,
                    "location": request.location,
                    "is_remote": request.is_remote,
                    "results_requested": request.results_wanted,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Successfully scraped {len(jobs_list)} jobs")
            return create_success_response(
                data=response_data.dict(),
                message=f"Successfully scraped {len(jobs_list)} jobs from {request.site_name.value}"
            )
            
        except Exception as e:
            error_msg = f"Failed to scrape jobs: {str(e)}"
            logger.error(error_msg)
            return create_error_response(
                error="Job scraping failed",
                message=error_msg
            )
    
    async def get_supported_sites(self) -> StandardResponse:
        """
        Get list of supported job sites for scraping.
        
        Returns:
            StandardResponse containing supported sites information
        """
        try:
            sites_info = {
                "indeed": {
                    "name": "Indeed",
                    "description": "Popular job board with extensive listings",
                    "supports_remote": True,
                    "supports_salary_filter": True
                },
                "linkedin": {
                    "name": "LinkedIn",
                    "description": "Professional networking platform with job listings",
                    "supports_remote": True,
                    "supports_salary_filter": False
                },
                "glassdoor": {
                    "name": "Glassdoor",
                    "description": "Job board with company reviews and salary data",
                    "supports_remote": True,
                    "supports_salary_filter": True
                },
                "ziprecruiter": {
                    "name": "ZipRecruiter",
                    "description": "Job board focused on quick applications",
                    "supports_remote": True,
                    "supports_salary_filter": True
                },
                "google": {
                    "name": "Google Jobs",
                    "description": "Google's job search aggregator",
                    "supports_remote": True,
                    "supports_salary_filter": False
                }
            }
            
            return create_success_response(
                data=sites_info,
                message="Supported job sites retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error getting supported sites: {str(e)}")
            return create_error_response(
                error="Failed to get supported sites",
                message=str(e)
            )


# Global service instance
jobspy_service = JobSpyIngestionService()


def get_jobspy_service() -> JobSpyIngestionService:
    """Get the global JobSpy ingestion service instance."""
    return jobspy_service