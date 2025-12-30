"""
Shared job scraping functions for use by both workers and ad-hoc endpoints.
Single source of truth for scraping logic.

Includes normalization utilities to ensure consistent job data formats across all sources.
"""
import asyncio
import random
import time
from typing import Dict, Any, Optional, List
import pandas as pd
from loguru import logger

from jobspy import scrape_jobs
from ...schemas.jobspy import JobSearchRequest, ScrapedJob
from ...schemas.responses import StandardResponse, create_success_response, create_error_response


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


def normalize_job_to_scraped_job(job_dict: Dict[str, Any], site_name: str = "unknown") -> ScrapedJob:
    """
    Normalize various job formats to standard ScrapedJob schema for database consistency.

    Handles different job structures from:
    - JobSpy direct scraping
    - LinkedIn CrewAI job search
    - LinkedIn recommended jobs
    - Other external sources

    Args:
        job_dict: Job data dictionary from any source
        site_name: Job site name for defaults

    Returns:
        Standardized ScrapedJob object compatible with database persistence
    """
    try:
        # Handle nested location structures (e.g. from LinkedIn results)
        location = job_dict.get("location", "")
        if isinstance(location, dict):
            # Convert {"city": "Seattle", "state": "WA", "country": "USA"} to "Seattle, WA, USA"
            city = location.get("city", "")
            state = location.get("state", "")
            country = location.get("country", "")
            parts = [part for part in [city, state, country] if part.strip()]
            location = ", ".join(parts)

        # Handle nested compensation/salary structures
        salary_min = salary_max = salary_source = interval = currency = None

        # Check for nested compensation object
        if "compensation" in job_dict and isinstance(job_dict["compensation"], dict):
            comp = job_dict["compensation"]
            salary_min = comp.get("min_amount", comp.get("min"))
            salary_max = comp.get("max_amount", comp.get("max"))
            currency = comp.get("currency", "USD")
            interval = comp.get("interval", "yearly")

        # Fallback to direct salary fields
        else:
            salary_min = job_dict.get("salary_min", job_dict.get("min_amount"))
            salary_max = job_dict.get("salary_max", job_dict.get("max_amount"))
            salary_source = job_dict.get("salary_source")
            interval = job_dict.get("interval", "yearly")

        # Handle different remote field names
        is_remote = job_dict.get("is_remote")
        if is_remote is None:
            is_remote = job_dict.get("remote", False)  # Handle LinkedIn's "remote" field

        # Ensure is_remote is boolean
        if isinstance(is_remote, str):
            is_remote = is_remote.lower() in ['true', '1', 'yes']

        # Parse and normalize date_posted if needed
        date_posted = job_dict.get("date_posted")
        if date_posted and not isinstance(date_posted, str):
            date_posted = _to_iso_date_str(date_posted)

        # Get description with multiple fallback field names
        description = (
            job_dict.get("job_description") or
            job_dict.get("description") or
            ""
        )

        return ScrapedJob(
            title=job_dict.get("title", "").strip(),
            company=job_dict.get("company", "").strip(),
            location=location.strip() if isinstance(location, str) else "",
            job_type=job_dict.get("job_type", job_dict.get("type", "")),
            date_posted=date_posted,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_source=salary_source,
            interval=interval,
            description=description,
            job_url=job_dict.get("job_url", "").strip(),
            job_url_direct=job_dict.get("job_url_direct", job_dict.get("job_url", "")).strip(),
            site=job_dict.get("site", site_name),
            emails=job_dict.get("emails", []) if isinstance(job_dict.get("emails"), list) else [],
            is_remote=is_remote
        )

    except Exception as e:
        logger.error(f"Failed to normalize job data from {site_name}: {e}")
        logger.debug(f"Job dict: {job_dict}")

        # Return minimal ScrapedJob on error to avoid crashes
        return ScrapedJob(
            title=job_dict.get("title", "Unknown Title"),
            company=job_dict.get("company", "Unknown Company"),
            location=str(job_dict.get("location", "Unknown Location")),
            description=f"Error normalizing job data: {str(e)}",
            job_url=job_dict.get("job_url", ""),
            site=site_name,
            is_remote=False
        )


def optimize_fresh_job_window(site_name: str, current_hour_window: Optional[int] = None) -> int:
    """
    Dynamically optimize the hours_old window for maximum fresh job results.

    Cycles through time windows to find the best balance of results vs freshness.

    Args:
        site_name: The job site being scraped
        current_hour_window: Current window being used (for cycling)

    Returns:
        Optimal hours_old value for fresh results
    """
    # Define fresh time windows to rotate through
    # Start with very fresh (1h) and expand if no results
    fresh_windows = [1, 3, 6, 12, 24, 48]

    # Site-specific optimizations (some sites have fresher content)
    site_optimals = {
        "linkedin": [1, 3, 6, 12, 24],  # LinkedIn often very fresh
        "indeed": [6, 12, 24, 48, 72],  # Indeed has more volume
        "glassdoor": [12, 24, 48, 72],  # Glassdoor posts less frequently
        "ziprecruiter": [6, 12, 24, 48], # Moderate freshness
        "google": [1, 3, 6, 12]  # Google Jobs often very fresh
    }

    available_windows = site_optimals.get(site_name, fresh_windows)

    # If no current window, start with middle value
    if current_hour_window is None:
        if not available_windows:
            logger.warning(f"No available windows for site '{site_name}', returning default value 24.")
            return 24  # Default fallback value
        return available_windows[len(available_windows) // 2]  # Middle value

    # Cycle to next window, wrap around if needed
    if current_hour_window in available_windows:
        current_idx = available_windows.index(current_hour_window)
        next_idx = (current_idx + 1) % len(available_windows)
        return available_windows[next_idx]

    # Fallback: find closest window
    closest_window = min(available_windows, key=lambda x: abs(x - (current_hour_window or 24)))
    logger.info(f"Optimized fresh window for {site_name}: {current_hour_window} -> {closest_window}")
    return closest_window


def scrape_jobs_sync(payload: Dict[str, Any], min_pause: int = 2, max_pause: int = 8) -> Dict[str, Any]:
    """
    Synchronous job scraping function - single source of truth.

    Implements pagination and fresh job optimization for maximum recent results.

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

    site_name = payload.get("site_name", "indeed")
    requested_results = payload.get("results_wanted", 15)

    # Optimize for fresh jobs - dynamically adjust hours_old if not specified
    if payload.get("hours_old") is None or payload.get("hours_old") == 0:
        optimal_hours = optimize_fresh_job_window(site_name)
        payload["hours_old"] = optimal_hours
        logger.info(f"Auto-optimized fresh window for {site_name}: {optimal_hours} hours")

    # For fresh jobs, we need more results due to date filters
    # Let's aim for 2-3x the requested amount to account for filtering
    results_needed = min(requested_results * 3, 100)  # Cap at 100 to avoid abuse

    # Build kwargs for jobspy from payload
    kwargs = {
        "site_name": site_name,
        "results_wanted": results_needed,  # Request more to account for date filtering
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
        
        # Support dynamic date replacement (e.g., {{yesterday}})
        if "{{yesterday}}" in google_q:
            from datetime import datetime, timedelta
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            google_q = google_q.replace("{{yesterday}}", yesterday)
            logger.info(f"Resolved {{yesterday}} in Google query: {google_q}")
            
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
        
        # Indeed/Glassdoor limitation: prioritize hours_old for recent jobs, then easy_apply, then job_type/is_remote
        if payload.get("hours_old") is not None:
            # Prioritize date filtering for recent jobs - don't remove it
            kwargs["hours_old"] = payload["hours_old"]
            # Remove conflicting easy_apply and job_type/is_remote when using hours_old
            kwargs.pop("easy_apply", None)
            kwargs.pop("job_type", None)
            kwargs.pop("is_remote", None)
        elif payload.get("easy_apply") is not None:
            kwargs["easy_apply"] = payload["easy_apply"]
            # Remove conflicting keys for easy_apply
            kwargs.pop("job_type", None)
            kwargs.pop("is_remote", None)
            
    elif site == "linkedin":
        if payload.get("linkedin_fetch_description") is not None:
            kwargs["linkedin_fetch_description"] = payload["linkedin_fetch_description"]
        if payload.get("linkedin_company_ids"):
            kwargs["linkedin_company_ids"] = payload["linkedin_company_ids"]
        
        # LinkedIn limitation: prioritize hours_old for recent jobs, then easy_apply
        if payload.get("hours_old") is not None:
            # Prioritize date filtering for recent jobs - don't remove it
            kwargs["hours_old"] = payload["hours_old"]
            # Remove conflicting easy_apply when using hours_old
            kwargs.pop("easy_apply", None)
        elif payload.get("easy_apply") is not None:
            kwargs["easy_apply"] = payload["easy_apply"]
            
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
