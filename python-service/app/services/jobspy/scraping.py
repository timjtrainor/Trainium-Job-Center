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


def scrape_jobs_sync(payload: Dict[str, Any], min_pause: int = 2, max_pause: int = 8) -> Dict[str, Any]:
    """
    Synchronous job scraping function - single source of truth.
    Implements pagination workarounds for JobSpy limitations.
    
    Args:
        payload: Dictionary containing scraping parameters (same format as JobSearchRequest)
        min_pause: Minimum pause between requests (seconds)  
        max_pause: Maximum pause between requests (seconds)
        
    Returns:
        Dictionary with scraping results and metadata
    """
    
    # Check if pagination mode is requested
    enable_pagination = payload.get("enable_pagination", False)
    max_results_target = payload.get("max_results_target", payload.get("results_wanted", 15))
    
    # If pagination is enabled and target is > 25, use multi-batch approach
    if enable_pagination and max_results_target > 25:
        logger.info(f"Pagination mode enabled - targeting {max_results_target} results")
        return _scrape_jobs_paginated(payload, min_pause, max_pause, max_results_target)
    
    # Standard single-batch scraping
    return _scrape_jobs_single_batch(payload, min_pause, max_pause)


def _scrape_jobs_single_batch(payload: Dict[str, Any], min_pause: int = 2, max_pause: int = 8) -> Dict[str, Any]:
    """Single batch scraping - original implementation."""
def _scrape_jobs_single_batch(payload: Dict[str, Any], min_pause: int = 2, max_pause: int = 8) -> Dict[str, Any]:
    """Single batch scraping - original implementation."""
    
    # Add random delay to simulate human-like behavior
    if min_pause > 0 or max_pause > 0:
        pause_time = random.uniform(min_pause, max_pause)
        logger.info(f"Adding human-like pause: {pause_time:.2f}s")
        time.sleep(pause_time)
    
    # Build kwargs for jobspy from payload
    kwargs = {
        "site_name": payload.get("site_name", "indeed"),
        "results_wanted": min(payload.get("results_wanted", 15), 100),  # Cap at 100 per JobSpy limits
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
    
    return _process_jobs_dataframe(jobs_df, site, payload, 1, 1, 0)


def _scrape_jobs_paginated(payload: Dict[str, Any], min_pause: int = 2, max_pause: int = 8, max_results_target: int = 100) -> Dict[str, Any]:
    """
    Paginated scraping using multiple strategies to overcome JobSpy limitations.
    
    Strategy 1: Time window splitting (recency filters)
    Strategy 2: Location variations (if applicable) 
    Strategy 3: Search term variations
    """
    
    site = payload.get("site_name", "indeed")
    logger.info(f"Starting paginated scrape for {site} - target: {max_results_target} results")
    
    all_jobs = []
    total_batches = 0
    total_errors = 0
    seen_urls = set()  # For deduplication
    
    # Strategy 1: Time window splitting (most effective)
    time_windows = [24, 72, 168, 720]  # 1 day, 3 days, 1 week, 1 month in hours
    
    for hours in time_windows:
        if len(all_jobs) >= max_results_target:
            break
            
        # Create payload for this time window  
        batch_payload = payload.copy()
        batch_payload["hours_old"] = hours
        batch_payload["results_wanted"] = min(50, max_results_target - len(all_jobs))  # Request up to 50 per batch
        
        logger.info(f"Batch {total_batches + 1}: Scraping jobs from last {hours} hours")
        
        try:
            batch_result = _scrape_jobs_single_batch(batch_payload, min_pause, max_pause)
            total_batches += 1
            
            if batch_result.get("jobs"):
                # Deduplicate by job_url
                new_jobs = []
                for job in batch_result["jobs"]:
                    job_url = job.job_url or job.job_url_direct
                    if job_url and job_url not in seen_urls:
                        seen_urls.add(job_url)
                        new_jobs.append(job)
                        
                all_jobs.extend(new_jobs)
                logger.info(f"Batch {total_batches}: Found {len(batch_result['jobs'])} jobs, {len(new_jobs)} new unique jobs")
            else:
                logger.info(f"Batch {total_batches}: No jobs found")
                
            total_errors += batch_result.get("errors_count", 0)
            
            # Add delay between batches to avoid rate limiting
            if len(all_jobs) < max_results_target:
                pause_time = random.uniform(min_pause * 2, max_pause * 2)  # Longer pause between batches
                logger.info(f"Inter-batch pause: {pause_time:.2f}s")
                time.sleep(pause_time)
                
        except Exception as e:
            logger.error(f"Error in batch {total_batches + 1}: {str(e)}")
            total_errors += 1
            total_batches += 1
            continue
    
    # Strategy 2: Location variations (if still need more results and location is flexible)
    if len(all_jobs) < max_results_target and payload.get("location"):
        location_variations = _generate_location_variations(payload.get("location"))
        
        for location in location_variations:
            if len(all_jobs) >= max_results_target:
                break
                
            batch_payload = payload.copy()
            batch_payload["location"] = location
            batch_payload["results_wanted"] = min(25, max_results_target - len(all_jobs))
            batch_payload.pop("hours_old", None)  # Remove time filter for location-based batches
            
            logger.info(f"Batch {total_batches + 1}: Trying location variation: {location}")
            
            try:
                batch_result = _scrape_jobs_single_batch(batch_payload, min_pause, max_pause)
                total_batches += 1
                
                if batch_result.get("jobs"):
                    new_jobs = []
                    for job in batch_result["jobs"]:
                        job_url = job.job_url or job.job_url_direct
                        if job_url and job_url not in seen_urls:
                            seen_urls.add(job_url)
                            new_jobs.append(job)
                            
                    all_jobs.extend(new_jobs)
                    logger.info(f"Location batch {total_batches}: Found {len(new_jobs)} new unique jobs")
                    
                total_errors += batch_result.get("errors_count", 0)
                
                if len(all_jobs) < max_results_target:
                    pause_time = random.uniform(min_pause * 2, max_pause * 2)
                    time.sleep(pause_time)
                    
            except Exception as e:
                logger.error(f"Error in location batch {total_batches + 1}: {str(e)}")
                total_errors += 1
                total_batches += 1
                continue
    
    # Calculate success metrics
    total_found = len(all_jobs)
    success_rate = (total_batches - total_errors) / total_batches if total_batches > 0 else 0
    
    # Determine status based on success rate and target achievement
    if total_found >= max_results_target * 0.8:  # Got at least 80% of target
        status = "succeeded"
    elif success_rate >= 0.5:
        status = "partial"
    else:
        status = "failed"
    
    result = {
        "status": status,
        "jobs": all_jobs,
        "total_found": total_found,
        "requested_pages": total_batches,
        "completed_pages": total_batches - total_errors,
        "errors_count": total_errors,
        "search_metadata": {
            "site": site,
            "search_params": payload,
            "success_rate": success_rate,
            "pagination_enabled": True,
            "target_results": max_results_target,
            "deduplication_stats": {
                "unique_urls_found": len(seen_urls),
                "duplicate_jobs_filtered": len(seen_urls) - total_found
            }
        },
        "message": f"Paginated scrape completed: {total_found} unique jobs from {total_batches} batches"
    }
    
    logger.info(f"Paginated scraping completed - Found {total_found} unique jobs across {total_batches} batches")
    return result


def _generate_location_variations(location: str) -> List[str]:
    """Generate location variations for broader searching."""
    variations = []
    
    # If it's a city, add state/country variations
    if "," in location:
        city_state = location.split(",")
        city = city_state[0].strip()
        state = city_state[1].strip()
        
        # Add nearby major cities in same state (basic heuristic)
        variations.extend([
            f"{state}",  # Just the state
            f"Remote",   # Remote jobs
        ])
        
        # Add some common major city variations if it's a US location
        if len(state) == 2:  # Likely US state abbreviation
            major_cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "San Francisco"]
            for major_city in major_cities:
                if major_city.lower() not in location.lower():
                    variations.append(f"{major_city}, {state}")
    else:
        # Single word location - add some common variations
        variations.extend([
            f"{location} Metro Area",
            f"Remote"
        ])
    
    return variations[:3]  # Limit to 3 variations to avoid too many requests


def _process_jobs_dataframe(jobs_df, site: str, payload: Dict[str, Any], 
                          requested_pages: int, completed_pages: int, errors_count: int) -> Dict[str, Any]:
    """Process JobSpy DataFrame into standardized response format."""
    
    # Convert pandas DataFrame to our response format
    jobs_list = []
    
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