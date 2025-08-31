"""
JobSpy ingestion service for scraping jobs from various job boards.
Integrates with the python-jobspy library to fetch job postings.
"""
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime
import pandas as pd
from loguru import logger

from jobspy import scrape_jobs
from ..core.config import get_settings
from ..models.responses import StandardResponse, create_success_response, create_error_response
from ..models.jobspy import JobSearchRequest, JobSearchResponse, ScrapedJob


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
            def _scrape_sync():
                return scrape_jobs(
                    site_name=request.site_name.value,
                    search_term=request.search_term,
                    location=request.location,
                    is_remote=request.is_remote,
                    job_type=request.job_type.value if request.job_type else None,
                    results_wanted=request.results_wanted,
                    distance=request.distance,
                    easy_apply=request.easy_apply,
                    hours_old=request.hours_old,
                    description_format="markdown",  # Keep consistent with existing app
                    verbose=1  # Enable some logging
                )
            
            # Run in thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            jobs_df = await loop.run_in_executor(None, _scrape_sync)
            
            # Convert pandas DataFrame to our response format
            jobs_list = []
            if not jobs_df.empty:
                for _, row in jobs_df.iterrows():
                    job = ScrapedJob(
                        title=row.get('title'),
                        company=row.get('company'),
                        location=row.get('location'),
                        job_type=row.get('job_type'),
                        date_posted=row.get('date_posted'),
                        salary_min=row.get('min_amount'),
                        salary_max=row.get('max_amount'),
                        salary_source=row.get('salary_source'),
                        interval=row.get('interval'),
                        description=row.get('description'),
                        job_url=row.get('job_url'),
                        job_url_direct=row.get('job_url_direct'),
                        site=row.get('site'),
                        emails=row.get('emails') if pd.notna(row.get('emails')) else None,
                        is_remote=row.get('is_remote')
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