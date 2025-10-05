"""
Job persistence service for storing scraped job data to PostgreSQL.
Handles idempotent upserts and batch processing with error handling.
"""
import asyncio
import hashlib
import re
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
import asyncpg
import json
from loguru import logger

from ...core.config import get_settings
from ...schemas.jobspy import ScrapedJob
from .database import get_database_service
from .company_normalization import normalize_company_name


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
        blocked_duplicates = 0
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
                        elif result == "duplicate_skipped":
                            blocked_duplicates += 1

                    except Exception as e:
                        error_msg = f"Record {i}: {str(e)}"
                        errors.append(error_msg)
                        logger.warning(f"Failed to persist job record {i}: {e}")

        summary = {
            "inserted": inserted,
            "skipped_duplicates": skipped_duplicates,  # Site+URL conflicts (same job from same site)
            "blocked_duplicates": blocked_duplicates,  # Canonical key conflicts (prevented from AI processing)
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

        # Generate canonical key for cross-site deduplication
        canonical_key = None
        if job.company and job.title:
            canonical_key = self._generate_canonical_key(job.title, job.company)

        # Generate content fingerprint for semantic deduplication
        fingerprint = None
        if job.description and len(job.description) > 100:
            fingerprint = self._generate_fingerprint(
                job.description,
                job.title or '',
                job.company or ''
            )

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
            "duplicate_group_id": None,  # Populated by post-processing job
            "duplicate_status": None  # Will be set during upsert based on canonical key check
        }
    
    async def _upsert_job(self, conn: asyncpg.Connection, job_data: Dict[str, Any]) -> str:
        """
        Perform preventive duplicate checking and upsert of job record.

        Args:
            conn: Database connection
            job_data: Mapped job data dictionary

        Returns:
            "inserted" if new record, "duplicate" if already exists, "duplicate_skipped" if prevented from insertion
        """
        # Check if this canonical key already exists (preventive deduplication)
        canonical_key = job_data.get("canonical_key")
        if canonical_key:
            existing = await conn.fetchval(
                "SELECT id FROM public.jobs WHERE canonical_key = $1 AND duplicate_status = 'original' LIMIT 1",
                canonical_key
            )
            if existing:
                # Insert this job as a duplicate that was blocked from processing
                duplicate_query = """
                INSERT INTO public.jobs (
                    site, job_url, title, company, company_url, location_country,
                    location_state, location_city, is_remote, job_type, compensation,
                    interval, min_amount, max_amount, currency, salary_source,
                    description, date_posted, ingested_at, source_raw, canonical_key,
                    fingerprint, duplicate_group_id, duplicate_status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                    $16, $17, $18, $19, $20, $21, $22, $23, $24
                ) ON CONFLICT (site, job_url) DO NOTHING
                """

                duplicate_result = await conn.execute(
                    duplicate_query,
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
                    job_data["duplicate_group_id"],
                    'duplicate_hidden'  # This is a duplicate that was prevented from processing
                )

                logger.info(f"Blocked duplicate job insertion: {canonical_key} (original already exists)")
                return "duplicate_skipped"

        # If no canonical duplicate found, proceed with normal upsert
        # Use INSERT ... ON CONFLICT DO NOTHING for idempotent behavior
        # This treats existing (site, job_url) as no-op per requirements
        query = """
        INSERT INTO public.jobs (
            site, job_url, title, company, company_url, location_country,
            location_state, location_city, is_remote, job_type, compensation,
            interval, min_amount, max_amount, currency, salary_source,
            description, date_posted, ingested_at, source_raw, canonical_key,
            fingerprint, duplicate_group_id, duplicate_status
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
            $16, $17, $18, $19, $20, $21, $22, $23, $24
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
                job_data["duplicate_group_id"],
                'original'  # This is the first/original instance
            )

            # Check if a row was actually inserted
            if result.split()[-1] == "1":  # "INSERT 0 1"
                logger.info(f"Inserted original job: {canonical_key}")
                return "inserted"
            else:  # "INSERT 0 0" - conflict occurred
                logger.info(f"Skipped duplicate job insertion (site+url conflict): {job_data['site']} - {job_data['job_url']}")
                return "duplicate"

        except Exception as e:
            logger.error(f"Database error during job upsert: {e}")
            raise

    def _generate_canonical_key(self, title: str, company: str) -> str:
        """
        Generate normalized canonical key for cross-site deduplication.

        Uses company normalization to handle large companies (Amazon/AWS, Microsoft/Azure, etc.)
        and title normalization to handle variations (Sr./Senior, PM/Product Manager).

        Args:
            title: Job title
            company: Company name

        Returns:
            Canonical key for deduplication (e.g., "amazon_senior_product_manager")
        """
        # Normalize company using alias mapping
        company_clean = normalize_company_name(company)

        # Normalize title
        title_clean = title.lower()

        # Expand common abbreviations
        title_clean = title_clean.replace('sr.', 'senior')
        title_clean = title_clean.replace('sr ', 'senior ')
        title_clean = title_clean.replace('jr.', 'junior')
        title_clean = title_clean.replace('jr ', 'junior ')
        title_clean = title_clean.replace(' mgr', ' manager')
        title_clean = title_clean.replace('mgr ', 'manager ')
        title_clean = title_clean.replace(' pm ', ' product manager ')
        title_clean = title_clean.replace(' eng ', ' engineer ')

        # Remove Roman numerals (I, II, III, IV, V)
        title_clean = re.sub(r'\b(i{1,3}|iv|v|vi{1,3})\b', '', title_clean)

        # Remove level numbers (1, 2, 3, etc.)
        title_clean = re.sub(r'\b\d+\b', '', title_clean)

        # Remove special characters and normalize whitespace
        title_clean = re.sub(r'[^a-z0-9\s]+', ' ', title_clean)
        title_clean = re.sub(r'\s+', '_', title_clean).strip('_')

        canonical = f"{company_clean}_{title_clean}"

        logger.debug(f"Canonical key: {company} + {title} → {canonical}")
        return canonical

    def _generate_fingerprint(self, description: str, title: str, company: str) -> str:
        """
        Generate content-based fingerprint for semantic duplicate detection.

        Uses shingling and hashing to detect jobs with similar descriptions
        even if posted on different sites with minor formatting differences.

        Args:
            description: Job description text
            title: Job title (for additional context)
            company: Company name (for additional context)

        Returns:
            MD5 hash fingerprint for content matching
        """
        # Normalize description text
        text = description.lower()

        # Remove HTML/markdown formatting
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[#*`_\[\]()]', '', text)

        # Remove common boilerplate phrases that vary between sites
        boilerplate_phrases = [
            'equal opportunity employer',
            'we are an equal',
            'apply now',
            'click here',
            'eeo statement',
            'apply today',
            'learn more',
            'submit resume',
            'send resume',
            'visit our website',
        ]
        for phrase in boilerplate_phrases:
            text = text.replace(phrase, '')

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Create word shingles (3-word sequences) for fuzzy matching
        words = text.split()
        if len(words) < 3:
            # Too short for shingling, just hash the whole thing
            combined = f"{company.lower()}_{title.lower()}_{text}"
            return hashlib.md5(combined.encode()).hexdigest()

        # Generate shingles
        shingles = []
        for i in range(len(words) - 2):
            shingle = ' '.join(words[i:i+3])
            shingles.append(shingle)

        # Sort and join shingles for consistent hashing
        shingle_text = '|'.join(sorted(set(shingles)))

        # Create final fingerprint with company and title context
        combined = f"{company.lower()}_{title.lower()}_{hashlib.sha256(shingle_text.encode()).hexdigest()[:16]}"
        fingerprint = hashlib.md5(combined.encode()).hexdigest()

        logger.debug(f"Fingerprint: {company} + {title} → {fingerprint}")
        return fingerprint

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
