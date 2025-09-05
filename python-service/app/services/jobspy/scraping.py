"""
Shared job scraping functions for use by both workers and ad-hoc endpoints.
Single source of truth for scraping logic.
"""
import asyncio
import random
import time
from typing import Dict, Any, Optional, List
import pandas as pd
from loguru import logger

from jobspy import scrape_jobs
from ...models.jobspy import JobSearchRequest, ScrapedJob
from ...models.responses import StandardResponse, create_success_response, create_error_response


def _to_iso_date_str(date_value) -> Optional[str]:
    """Convert date to ISO string format."""
    if pd.isna(date_value) or date_value is None:
        return None
    
    try:
        if isinstance(date_value, str):
            return date_value
        # Convert pandas timestamp to ISO string
        return date_value.isoformat() if hasattr(date_value, 'isoformat') else str(date_value)
    except:
        return None


def scrape_jobs_sync(payload: Dict[str, Any], min_pause: int = 2, max_pause: int = 8) -> Dict[str, Any]:
    """
    Synchronous job scraping function - single source of truth.
    
    Args:
        payload: Dictionary containing scraping parameters (same format as JobSearchRequest)
        min_pause: Minimum pause between requests (seconds)  
        max_pause: Maximum pause between requests (seconds)
        
    Returns:
        Dictionary with scraping results and metadata
    """
    
    # Add random delay to simulate human-like behavior
    if min_pause > 0 or max_pause > 0:
        pause_time = random.uniform(min_pause, max_pause)
        logger.info(f"Adding human-like pause: {pause_time:.2f}s")
        time.sleep(pause_time)
    
    # Build kwargs for jobspy from payload
    kwargs = {
        "site_name": payload.get("site_name", "indeed"),
        "results_wanted": payload.get("results_wanted", 15),
        "description_format": "markdown",
        "verbose": 1,
    }
    
    # Add common parameters if present
    if "search_term" in payload and payload["search_term"]:
        kwargs["search_term"] = payload["search_term"]
    if "location" in payload and payload["location"]:
        kwargs["location"] = payload["location"]
    if "is_remote" in payload:
        kwargs["is_remote"] = payload["is_remote"]
    if "job_type" in payload and payload["job_type"]:
        kwargs["job_type"] = payload["job_type"]
    if "distance" in payload and payload["distance"]:
        kwargs["distance"] = payload["distance"]
    if "easy_apply" in payload and payload["easy_apply"] is not None:
        kwargs["easy_apply"] = payload["easy_apply"]
    if "hours_old" in payload and payload["hours_old"] is not None:
        kwargs["hours_old"] = payload["hours_old"]
    
    site = payload.get("site_name", "indeed")
    
    # Site-specific parameter handling
    if site == "google":
        # Google: only google_search_term is honored
        google_q = payload.get("google_search_term")
        if not google_q:
            # Fallback: synthesize a decent Google query
            parts = []
            if payload.get("search_term"):
                parts.append(payload["search_term"])
            if payload.get("location"):
                parts.append(f"jobs near {payload['location']}")
            if payload.get("hours_old"):
                parts.append(f"posted last {int(payload['hours_old'])} hours")
            google_q = " ".join(parts).strip() or "software engineer jobs"
        kwargs["google_search_term"] = google_q
        
        # Remove incompatible parameters for Google
        kwargs.pop("search_term", None)
        kwargs.pop("location", None)
        kwargs.pop("job_type", None)
        kwargs.pop("is_remote", None)
        kwargs.pop("hours_old", None)
        kwargs.pop("easy_apply", None)
        
    elif site in ["indeed", "glassdoor"]:
        # country_indeed is required for these sites
        country = payload.get("country_indeed", "USA") 
        if country:
            kwargs["country_indeed"] = country
        
        # Indeed/Glassdoor limitation: only one of {hours_old} OR {job_type/is_remote} OR {easy_apply}
        if payload.get("easy_apply") is not None:
            kwargs["easy_apply"] = payload["easy_apply"]
            # enforce "only one" by removing conflicting keys
            kwargs.pop("hours_old", None)
            kwargs.pop("job_type", None)
            kwargs.pop("is_remote", None)
            
    elif site == "linkedin":
        if payload.get("linkedin_fetch_description") is not None:
            kwargs["linkedin_fetch_description"] = payload["linkedin_fetch_description"]
        if payload.get("linkedin_company_ids"):
            kwargs["linkedin_company_ids"] = payload["linkedin_company_ids"]
        
        # LinkedIn limitation: only one of {hours_old} OR {easy_apply}
        if payload.get("easy_apply") is not None:
            kwargs["easy_apply"] = payload["easy_apply"]
            kwargs.pop("hours_old", None)
            
    elif site == "ziprecruiter":
        # no special params beyond the general ones
        pass
    
    logger.info(f"Scraping {site} with parameters: {kwargs}")
    
    # Execute the scraping
    jobs_df = scrape_jobs(**kwargs)
    
    # Convert pandas DataFrame to our response format
    jobs_list = []
    requested_pages = 1  # JobSpy handles pagination internally
    completed_pages = 1
    errors_count = 0
    
    if jobs_df is not None and not jobs_df.empty:
        for _, row in jobs_df.iterrows():
            try:
                job = ScrapedJob(
                    title=row.get("title"),
                    company=row.get("company"),
                    location=row.get("location") if pd.notna(row.get("location")) else None,
                    job_type=(row.get("job_type") if pd.notna(row.get("job_type")) else None),
                    date_posted=_to_iso_date_str(row.get("date_posted")),
                    salary_min=(row.get("min_amount") if pd.notna(row.get("min_amount")) else None),
                    salary_max=(row.get("max_amount") if pd.notna(row.get("max_amount")) else None),
                    salary_source=(row.get("salary_source") if pd.notna(row.get("salary_source")) else None),
                    interval=(row.get("interval") if pd.notna(row.get("interval")) else None),
                    description=row.get("description"),
                    job_url=row.get("job_url"),
                    job_url_direct=row.get("job_url_direct"),
                    site=row.get("site"),
                    emails=row.get("emails", []) if pd.notna(row.get("emails")) else None,
                    is_remote=row.get("is_remote") if pd.notna(row.get("is_remote")) else None,
                )
                jobs_list.append(job)
            except Exception as e:
                logger.warning(f"Failed to parse job row: {str(e)}")
                errors_count += 1
    else:
        logger.warning("No jobs found or empty DataFrame returned")
    
    # Calculate success metrics
    total_found = len(jobs_list)
    success_rate = (completed_pages - errors_count) / completed_pages if completed_pages > 0 else 0
    
    # Determine status based on success rate
    if success_rate >= 0.7:
        status = "succeeded"
    elif success_rate >= 0.3:
        status = "partial"
    else:
        status = "failed"
    
    return {
        "status": status,
        "jobs": jobs_list,
        "total_found": total_found,
        "requested_pages": requested_pages,
        "completed_pages": completed_pages,
        "errors_count": errors_count,
        "search_metadata": {
            "site": site,
            "search_params": payload,
            "success_rate": success_rate
        },
        "message": f"Scraped {total_found} jobs from {site}" if total_found > 0 else f"No jobs found on {site}"
    }


async def scrape_jobs_async(payload: Dict[str, Any], min_pause: int = 2, max_pause: int = 8) -> Dict[str, Any]:
    """
    Asynchronous wrapper for job scraping function.
    
    Args:
        payload: Dictionary containing scraping parameters
        min_pause: Minimum pause between requests (seconds)
        max_pause: Maximum pause between requests (seconds)
        
    Returns:
        Dictionary with scraping results and metadata
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, scrape_jobs_sync, payload, min_pause, max_pause)