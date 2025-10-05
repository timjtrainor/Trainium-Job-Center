"""
API endpoints for enriching Glassdoor jobs with full descriptions.

Provides on-demand scraping and batch backfill capabilities.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

from ....services.jobspy.glassdoor_scraper import (
    scrape_glassdoor_job_description,
    enrich_glassdoor_job_with_description,
    PLAYWRIGHT_AVAILABLE
)
from ....services.infrastructure.database import get_database_service

router = APIRouter(prefix="/glassdoor-enrichment", tags=["Glassdoor Enrichment"])


class EnrichJobRequest(BaseModel):
    job_id: str


class EnrichJobResponse(BaseModel):
    success: bool
    job_id: str
    description_length: Optional[int] = None
    message: str


@router.post("/enrich-job/{job_id}", response_model=EnrichJobResponse)
async def enrich_single_job(job_id: str):
    """
    Scrape and save full job description for a single Glassdoor job.

    Args:
        job_id: UUID of job to enrich

    Returns:
        Status and description length
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    db_service = get_database_service()
    await db_service.initialize()

    try:
        # Get job from database
        job = await db_service.get_job(job_id)

        if not job:
            raise HTTPException(404, f"Job {job_id} not found")

        if not job.get('site') or job.get('site').lower() != 'glassdoor':
            raise HTTPException(400, "Job is not from Glassdoor")

        if job.get('description') or job.get('scraped_markdown'):
            return EnrichJobResponse(
                success=True,
                job_id=job_id,
                description_length=len(job.get('description') or job.get('scraped_markdown')),
                message="Job already has description"
            )

        job_url = job.get('url') or job.get('job_url')
        if not job_url:
            raise HTTPException(400, "Job has no URL to scrape")

        # Scrape description
        logger.info(f"Enriching job {job_id} from {job_url}")
        description = await scrape_glassdoor_job_description(job_url)

        if not description:
            raise HTTPException(500, "Failed to scrape job description")

        # Update database (only description field for now)
        await db_service.update_job(job_id, {
            'description': description
        })

        logger.info(f"Successfully enriched job {job_id} with {len(description)} char description")

        return EnrichJobResponse(
            success=True,
            job_id=job_id,
            description_length=len(description),
            message="Job enriched successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enrich job {job_id}: {e}")
        raise HTTPException(500, str(e))


@router.post("/backfill-all")
async def backfill_all_glassdoor_jobs(
    background_tasks: BackgroundTasks,
    limit: Optional[int] = None
):
    """
    Backfill descriptions for all Glassdoor jobs missing descriptions.

    Runs in background to avoid timeout. Use with caution - can take hours for many jobs.

    Args:
        limit: Max number of jobs to process (None = all)

    Returns:
        Status message
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    db_service = get_database_service()
    await db_service.initialize()

    try:
        # Get count of jobs to process
        async with db_service.pool.acquire() as conn:
            count_query = """
            SELECT COUNT(*)
            FROM jobs
            WHERE LOWER(site) = 'glassdoor'
              AND (description IS NULL OR description = '')
              AND job_url IS NOT NULL
            """
            if limit:
                count_query += f" LIMIT {limit}"

            total_jobs = await conn.fetchval(count_query)

        if total_jobs == 0:
            return {
                "success": True,
                "message": "No Glassdoor jobs need enrichment",
                "jobs_queued": 0
            }

        # Queue background task
        background_tasks.add_task(
            _backfill_glassdoor_descriptions,
            limit
        )

        return {
            "success": True,
            "message": f"Backfill task started for {total_jobs} Glassdoor jobs",
            "jobs_queued": total_jobs,
            "note": "This will run in the background. Check logs for progress."
        }

    except Exception as e:
        logger.error(f"Failed to start backfill: {e}")
        raise HTTPException(500, str(e))


async def _backfill_glassdoor_descriptions(limit: Optional[int] = None):
    """
    Background task to backfill Glassdoor job descriptions.

    Args:
        limit: Max number of jobs to process
    """
    db_service = get_database_service()
    await db_service.initialize()

    try:
        logger.info(f"Starting Glassdoor description backfill (limit={limit})")

        # Get jobs needing enrichment
        async with db_service.pool.acquire() as conn:
            query = """
            SELECT id, job_url, title, company
            FROM jobs
            WHERE LOWER(site) = 'glassdoor'
              AND (description IS NULL OR description = '')
              AND job_url IS NOT NULL
            ORDER BY date_posted DESC
            """
            if limit:
                query += f" LIMIT {limit}"

            jobs = await conn.fetch(query)

        total = len(jobs)
        logger.info(f"Found {total} Glassdoor jobs to enrich")

        success_count = 0
        fail_count = 0

        for i, job in enumerate(jobs, 1):
            job_id = str(job['id'])
            job_url = job['job_url']

            try:
                logger.info(f"[{i}/{total}] Enriching {job['title']} at {job['company']}")

                description = await scrape_glassdoor_job_description(job_url)

                if description:
                    await db_service.update_job(job_id, {
                        'description': description
                    })
                    success_count += 1
                    logger.info(f"✓ [{i}/{total}] Success: {len(description)} chars")
                else:
                    fail_count += 1
                    logger.warning(f"✗ [{i}/{total}] Failed to scrape")

                # Rate limiting: wait 2 seconds between requests
                await asyncio.sleep(2)

            except Exception as e:
                fail_count += 1
                logger.error(f"✗ [{i}/{total}] Error enriching job {job_id}: {e}")
                continue

        logger.info(f"Backfill complete: {success_count} success, {fail_count} failed out of {total} total")

    except Exception as e:
        logger.error(f"Backfill task failed: {e}")


@router.get("/status")
async def get_enrichment_status():
    """
    Get statistics on Glassdoor job description enrichment status.

    Returns:
        Counts of total, enriched, and pending Glassdoor jobs
    """
    db_service = get_database_service()
    await db_service.initialize()

    try:
        async with db_service.pool.acquire() as conn:
            total = await conn.fetchval("""
                SELECT COUNT(*)
                FROM jobs
                WHERE LOWER(site) = 'glassdoor'
            """)

            enriched = await conn.fetchval("""
                SELECT COUNT(*)
                FROM jobs
                WHERE LOWER(site) = 'glassdoor'
                  AND (description IS NOT NULL AND description != '')
            """)

            pending = total - enriched

        return {
            "total_glassdoor_jobs": total,
            "enriched_with_description": enriched,
            "pending_enrichment": pending,
            "enrichment_percentage": round((enriched / total * 100), 2) if total > 0 else 0
        }

    except Exception as e:
        logger.error(f"Failed to get enrichment status: {e}")
        raise HTTPException(500, str(e))


import asyncio  # Import for sleep in backfill
