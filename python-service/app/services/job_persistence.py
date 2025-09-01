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

from ..core.config import get_settings
from ..models.jobspy import ScrapedJob
from .database import get_database_service


class JobPersistenceService:
    """Service for persisting scraped job data with idempotent upserts."""
    
    def __init__(self):
        self.db_service = get_database_service()
    
    async def persist_jobs(self, 
                          records: List[Union[ScrapedJob, Dict[str, Any]]], 
                          site_name: str) -> Dict[str, Any]:
        """
        Persist scraped jobs to the database with idempotent upserts.
        
        Args:
            records: List of ScrapedJob objects or dictionaries
            site_name: Name of the job site (indeed, linkedin, etc.)
            
        Returns:
            Summary dict: {inserted: int, skipped_duplicates: int, errors: List[str]}
        """
        if not records:
            return {"inserted": 0, "skipped_duplicates": 0, "errors": []}
        
        # Initialize database service if needed
        if not self.db_service.initialized:
            await self.db_service.initialize()
        
        logger.info(f"Starting persistence of {len(records)} jobs from {site_name}")
        
        inserted = 0
        skipped_duplicates = 0
        errors = []
        
        async with self.db_service.pool.acquire() as conn:
            async with conn.transaction():
                for i, record in enumerate(records):
                    try:
                        # Convert to ScrapedJob if it's a dict
                        if isinstance(record, dict):
                            job = ScrapedJob(**record)
                        else:
                            job = record
                        
                        # Validate required fields
                        if not job.job_url:
                            errors.append(f"Record {i}: missing job_url")
                            continue
                        if not job.title:
                            errors.append(f"Record {i}: missing title")
                            continue
                            
                        # Map ScrapedJob to database fields
                        job_data = self._map_job_to_db(job, site_name)
                        
                        # Attempt upsert
                        result = await self._upsert_job(conn, job_data)
                        
                        if result == "inserted":
                            inserted += 1
                        elif result == "duplicate":
                            skipped_duplicates += 1
                            
                    except Exception as e:
                        error_msg = f"Record {i}: {str(e)}"
                        errors.append(error_msg)
                        logger.warning(f"Failed to persist job record {i}: {e}")
        
        summary = {
            "inserted": inserted,
            "skipped_duplicates": skipped_duplicates,
            "errors": errors
        }
        
        logger.info(f"Persistence complete: {summary}")
        return summary
    
    def _map_job_to_db(self, job: ScrapedJob, site_name: str) -> Dict[str, Any]:
        """
        Map a ScrapedJob object to database fields.
        
        Args:
            job: ScrapedJob object
            site_name: Job site name
            
        Returns:
            Dictionary of database field values
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
        
        # Create source_raw with the complete job data for provenance
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
            "scraped_at": datetime.now(timezone.utc).isoformat()
        }
        
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
            "canonical_key": None,     # Future: deduplication key
            "fingerprint": None,       # Future: content hash
            "duplicate_group_id": None # Future: cross-board grouping
        }
    
    async def _upsert_job(self, conn: asyncpg.Connection, job_data: Dict[str, Any]) -> str:
        """
        Perform idempotent upsert of job record.
        
        Args:
            conn: Database connection
            job_data: Mapped job data dictionary
            
        Returns:
            "inserted" if new record, "duplicate" if already exists
        """
        # Use INSERT ... ON CONFLICT DO NOTHING for idempotent behavior
        # This treats existing (site, job_url) as no-op per requirements
        query = """
        INSERT INTO public.jobs (
            site, job_url, title, company, company_url, location_country, 
            location_state, location_city, is_remote, job_type, compensation,
            interval, min_amount, max_amount, currency, salary_source, 
            description, date_posted, ingested_at, source_raw, canonical_key,
            fingerprint, duplicate_group_id
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, 
            $16, $17, $18, $19, $20, $21, $22, $23
        ) ON CONFLICT (site, job_url) DO NOTHING
        """
        
        try:
            result = await conn.execute(
                query,
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
            
            # Check if a row was actually inserted
            if result.split()[-1] == "1":  # "INSERT 0 1"
                return "inserted"
            else:  # "INSERT 0 0" - conflict occurred
                return "duplicate"
                
        except Exception as e:
            logger.error(f"Database error during job upsert: {e}")
            raise


# Global instance
_job_persistence_service: Optional[JobPersistenceService] = None

def get_job_persistence_service() -> JobPersistenceService:
    """Get or create the global job persistence service instance."""
    global _job_persistence_service
    if _job_persistence_service is None:
        _job_persistence_service = JobPersistenceService()
    return _job_persistence_service


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