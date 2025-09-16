"""
Job persistence service for storing scraped job data to PostgreSQL.
Handles idempotent upserts and batch processing with error handling.
"""
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
import asyncpg
import json
from loguru import logger

from ...core.config import get_settings
from ...schemas.jobspy import ScrapedJob
from .database import get_database_service


class JobPersistenceService:
    """Service for persisting scraped job data with idempotent upserts."""
    
    def __init__(self):
        self.db_service = get_database_service()
    
    async def persist_jobs(self, 
                          records: List[Union[ScrapedJob, Dict[str, Any]]], 
                          site_name: str) -> Dict[str, Any]:
        """
        Persist scraped jobs to the database with enhanced deduplication.
        
        Args:
            records: List of ScrapedJob objects or dictionaries
            site_name: Name of the job site (indeed, linkedin, etc.)
            
        Returns:
            Summary dict: {inserted: int, skipped_duplicates: int, updated: int, errors: List[str]}
        """
        if not records:
            return {"inserted": 0, "skipped_duplicates": 0, "updated": 0, "errors": []}
        
        # Initialize database service if needed
        if not self.db_service.initialized:
            await self.db_service.initialize()
        
        logger.info(f"Starting enhanced persistence of {len(records)} jobs from {site_name}")
        
        inserted = 0
        skipped_duplicates = 0
        updated = 0
        errors = []
        
        # Pre-process records for deduplication
        dedupe_stats = self._deduplicate_records(records)
        logger.info(f"Deduplication: {dedupe_stats}")
        
        unique_records = dedupe_stats["unique_records"]
        
        async with self.db_service.pool.acquire() as conn:
            async with conn.transaction():
                for i, record in enumerate(unique_records):
                    try:
                        # Convert to ScrapedJob if it's a dict
                        if isinstance(record, dict):
                            job = ScrapedJob(**record)
                        else:
                            job = record
                        
                        # Validate required fields
                        validation_error = self._validate_job_record(job, i)
                        if validation_error:
                            errors.append(validation_error)
                            continue
                            
                        # Map ScrapedJob to database fields with enhanced metadata
                        job_data = self._map_job_to_db_enhanced(job, site_name)
                        
                        # Attempt enhanced upsert with update detection
                        result = await self._upsert_job_enhanced(conn, job_data)
                        
                        if result == "inserted":
                            inserted += 1
                        elif result == "duplicate":
                            skipped_duplicates += 1
                        elif result == "updated":
                            updated += 1
                            
                    except Exception as e:
                        error_msg = f"Record {i}: {str(e)}"
                        errors.append(error_msg)
                        logger.warning(f"Failed to persist job record {i}: {e}")
        
        summary = {
            "inserted": inserted,
            "skipped_duplicates": skipped_duplicates,
            "updated": updated,
            "errors": errors,
            "deduplication": dedupe_stats
        }
        
        logger.info(f"Enhanced persistence complete: {summary}")
        return summary
    
    def _deduplicate_records(self, records: List[Union[ScrapedJob, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Deduplicate records before database insertion.
        
        Returns:
            Dict with unique_records list and statistics
        """
        seen_urls = set()
        seen_fingerprints = set()
        unique_records = []
        url_duplicates = 0
        content_duplicates = 0
        
        for record in records:
            # Get job data
            if isinstance(record, dict):
                job_url = record.get("job_url")
                title = record.get("title", "")
                company = record.get("company", "")
                description = record.get("description", "")
            else:
                job_url = record.job_url
                title = record.title or ""
                company = record.company or ""
                description = record.description or ""
            
            # Skip records without URL (can't dedupe)
            if not job_url:
                continue
                
            # Check URL-based deduplication
            if job_url in seen_urls:
                url_duplicates += 1
                continue
            
            # Create content fingerprint for cross-URL deduplication
            content_parts = [
                title.lower().strip(),
                company.lower().strip(),
                (description[:200].lower().strip() if description else "")
            ]
            fingerprint = "|".join(content_parts)
            
            # Check content-based deduplication
            if fingerprint in seen_fingerprints:
                content_duplicates += 1
                continue
                
            # Record is unique
            seen_urls.add(job_url)
            seen_fingerprints.add(fingerprint)
            unique_records.append(record)
        
        return {
            "unique_records": unique_records,
            "original_count": len(records),
            "unique_count": len(unique_records),
            "url_duplicates_removed": url_duplicates,
            "content_duplicates_removed": content_duplicates,
            "total_duplicates_removed": url_duplicates + content_duplicates
        }
    
    def _validate_job_record(self, job: ScrapedJob, index: int) -> Optional[str]:
        """
        Validate a job record for required fields.
        
        Returns:
            Error message if validation fails, None if valid
        """
        if not job.job_url:
            return f"Record {index}: missing job_url"
        if not job.title:
            return f"Record {index}: missing title"
        if not job.company:
            return f"Record {index}: missing company name"
        return None
    
    def _map_job_to_db_enhanced(self, job: ScrapedJob, site_name: str) -> Dict[str, Any]:
        """
        Map a ScrapedJob object to database fields with enhanced metadata.
        
        Args:
            job: ScrapedJob object
            site_name: Job site name
            
        Returns:
            Dictionary of database field values with enhanced tracking
        """
        # Parse date_posted if it's a string
        date_posted = None
        if job.date_posted:
            try:
                # Handle ISO date strings
                if isinstance(job.date_posted, str):
                    # Try parsing as ISO date first
                    try:
                        date_posted = datetime.fromisoformat(job.date_posted.replace('Z', '+00:00'))
                    except ValueError:
                        # Fallback to other common formats if needed
                        logger.warning(f"Could not parse date_posted: {job.date_posted}")
                else:
                    date_posted = job.date_posted
            except Exception as e:
                logger.warning(f"Date parsing error for {job.date_posted}: {e}")
        
        # Create enhanced source_raw with additional metadata
        source_raw = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "job_type": job.job_type,
            "date_posted": job.date_posted,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_source": job.salary_source,
            "interval": job.interval,
            "description": job.description,
            "job_url": job.job_url,
            "job_url_direct": job.job_url_direct,
            "site": job.site,
            "emails": job.emails,
            "is_remote": job.is_remote,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "scraper_version": "jobspy_v1.1.82_enhanced"
        }
        
        # Generate content fingerprint for deduplication
        fingerprint_parts = [
            (job.title or "").lower().strip(),
            (job.company or "").lower().strip(),
            (job.description[:200] if job.description else "").lower().strip()
        ]
        fingerprint = "|".join(fingerprint_parts)
        
        # Generate canonical key (future: cross-site deduplication)
        canonical_key = f"{site_name}:{job.job_url}"
        
        return {
            "site": site_name,
            "job_url": job.job_url,
            "title": job.title,
            "company": job.company,
            "company_url": None,  # Not available from JobSpy currently
            "location_country": None,  # Future: parse from job.location
            "location_state": None,    # Future: parse from job.location  
            "location_city": None,     # Future: parse from job.location
            "is_remote": job.is_remote,
            "job_type": job.job_type,
            "compensation": None,  # Future: format from min/max/interval
            "interval": job.interval,
            "min_amount": job.salary_min,
            "max_amount": job.salary_max,
            "currency": None,  # Future: extract from JobSpy data
            "salary_source": job.salary_source,
            "description": job.description,
            "date_posted": date_posted,
            "ingested_at": datetime.now(timezone.utc),
            "source_raw": source_raw,
            "canonical_key": canonical_key,
            "fingerprint": fingerprint,
            "duplicate_group_id": None # Future: cross-board grouping
        }
    
    async def _upsert_job_enhanced(self, conn: asyncpg.Connection, job_data: Dict[str, Any]) -> str:
        """
        Perform enhanced upsert with update detection and improved conflict handling.
        
        Args:
            conn: Database connection
            job_data: Mapped job data dictionary
            
        Returns:
            "inserted" if new record, "duplicate" if unchanged, "updated" if modified
        """
        # First, try to check if record exists and needs updating
        check_query = """
        SELECT id, fingerprint, ingested_at 
        FROM public.jobs 
        WHERE site = $1 AND job_url = $2
        """
        
        existing = await conn.fetchrow(check_query, job_data["site"], job_data["job_url"])
        
        if existing:
            # Check if content has changed (fingerprint-based)
            if existing["fingerprint"] == job_data["fingerprint"]:
                logger.debug(f"Job unchanged: {job_data['job_url']}")
                return "duplicate"
            else:
                # Content has changed, update the record
                update_query = """
                UPDATE public.jobs SET
                    title = $3, company = $4, company_url = $5, location_country = $6,
                    location_state = $7, location_city = $8, is_remote = $9, job_type = $10,
                    compensation = $11, interval = $12, min_amount = $13, max_amount = $14,
                    currency = $15, salary_source = $16, description = $17, date_posted = $18,
                    ingested_at = $19, source_raw = $20, canonical_key = $21,
                    fingerprint = $22, duplicate_group_id = $23
                WHERE site = $1 AND job_url = $2
                """
                
                await conn.execute(
                    update_query,
                    job_data["site"],
                    job_data["job_url"],
                    job_data["title"],
                    job_data["company"],
                    job_data["company_url"],
                    job_data["location_country"],
                    job_data["location_state"],
                    job_data["location_city"],
                    job_data["is_remote"],
                    job_data["job_type"],
                    job_data["compensation"],
                    job_data["interval"],
                    job_data["min_amount"],
                    job_data["max_amount"],
                    job_data["currency"],
                    job_data["salary_source"],
                    job_data["description"],
                    job_data["date_posted"],
                    job_data["ingested_at"],
                    json.dumps(job_data["source_raw"]),
                    job_data["canonical_key"],
                    job_data["fingerprint"],
                    job_data["duplicate_group_id"]
                )
                
                logger.debug(f"Job updated: {job_data['job_url']}")
                return "updated"
        else:
            # Record doesn't exist, insert it
            insert_query = """
            INSERT INTO public.jobs (
                site, job_url, title, company, company_url, location_country, 
                location_state, location_city, is_remote, job_type, compensation,
                interval, min_amount, max_amount, currency, salary_source, 
                description, date_posted, ingested_at, source_raw, canonical_key,
                fingerprint, duplicate_group_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, 
                $16, $17, $18, $19, $20, $21, $22, $23
            )
            """
            
            await conn.execute(
                insert_query,
                job_data["site"],
                job_data["job_url"],
                job_data["title"],
                job_data["company"],
                job_data["company_url"],
                job_data["location_country"],
                job_data["location_state"],
                job_data["location_city"],
                job_data["is_remote"],
                job_data["job_type"],
                job_data["compensation"],
                job_data["interval"],
                job_data["min_amount"],
                job_data["max_amount"],
                job_data["currency"],
                job_data["salary_source"],
                job_data["description"],
                job_data["date_posted"],
                job_data["ingested_at"],
                json.dumps(job_data["source_raw"]),
                job_data["canonical_key"],
                job_data["fingerprint"],
                job_data["duplicate_group_id"]
            )
            
            logger.debug(f"Job inserted: {job_data['job_url']}")
            return "inserted"

def get_job_persistence_service() -> JobPersistenceService:
    """Create a new job persistence service instance."""
    return JobPersistenceService()


async def persist_jobs(records: List[Union[ScrapedJob, Dict[str, Any]]], 
                      site_name: str) -> Dict[str, Any]:
    """
    Convenience function for persisting jobs.
    
    Args:
        records: List of ScrapedJob objects or dictionaries
        site_name: Job site name (indeed, linkedin, etc.)
        
    Returns:
        Summary: {inserted: int, skipped_duplicates: int, errors: List[str]}
    """
    service = get_job_persistence_service()
    return await service.persist_jobs(records, site_name)

