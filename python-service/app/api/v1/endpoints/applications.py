"""Application generation endpoints for LinkedIn workflow."""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger
import json
import re

from ....services.infrastructure.database import get_database_service, DatabaseService
from ....services.ai.application_generator import get_application_generator
from ....core.config import get_settings
from ....services.infrastructure.company_normalization import normalize_company_name

router = APIRouter(prefix="/applications", tags=["Applications"])

# Get settings for default user_id
settings = get_settings()


def format_job_location(job: Dict[str, Any]) -> str:
    """Format job location from separate database fields into a single string."""
    city = (job.get('location_city') or '').strip()
    state = (job.get('location_state') or '').strip()
    country = (job.get('location_country') or '').strip()

    parts = [part for part in [city, state, country] if part]
    if parts:
        return ', '.join(parts)

    # Fallback to any generic location field
    return (job.get('location') or '').strip()


def format_job_salary(job: Dict[str, Any]) -> Optional[str]:
    """Format job salary range from min/max amounts."""
    min_amount = job.get('salary_min')
    max_amount = job.get('salary_max')
    currency = job.get('currency', 'USD')

    if min_amount is not None or max_amount is not None:
        min_str = f"{min_amount:,}" if min_amount else ""
        max_str = f"{max_amount:,}" if max_amount else ""

        if min_str and max_str:
            return f"${min_str}-${max_str}"
        elif min_str:
            return f"${min_str}+"
        elif max_str:
            return f"Up to ${max_str}"

    return None


class ApplicationResponse(BaseModel):
    success: bool
    application_id: str
    message: str


async def _ensure_job_company(
    job: Dict[str, Any],
    job_id: str,
    db_service: DatabaseService
) -> Optional[str]:
    """Ensure the job has a company_id by matching or creating a company record."""

    company_id = job.get("company_id")
    if company_id:
        return str(company_id)

    company_name = job.get("company_name") or job.get("company")
    if not company_name:
        return None

    normalized_name = normalize_company_name(company_name)
    if not normalized_name:
        return None

    # First check if company with exact name already exists (unique constraint)
    await db_service.initialize()  # Ensure pool is ready
    async with db_service.pool.acquire() as conn:
        exact_match = await conn.fetchrow("""
            SELECT company_id, company_name
            FROM companies
            WHERE company_name = $1
            LIMIT 1
        """, company_name)

    if exact_match:
        company_id = str(exact_match["company_id"])
        # Update job with the existing company
        await db_service.update_job(job_id, {
            "company_id": company_id,
            "company_name": company_name,
            "normalized_company": normalized_name,
        })
        job["company_id"] = company_id
        job.setdefault("company_name", company_name)
        return company_id

    # If no exact match, try normalized name matching (if column exists)
    existing_company = await db_service.get_company_by_normalized_name(normalized_name, None)
    if existing_company:
        company_id = existing_company.get("company_id")
        # Update company name to be consistent if different, then update job
        if company_id:
            current_name = existing_company.get("company_name", "")
            if current_name != company_name:
                await db_service.update_company(company_id, {"company_name": company_name})
            await db_service.update_job(job_id, {
                "company_id": company_id,
                "company_name": company_name,
                "normalized_company": normalized_name,
            })
            job["company_id"] = company_id
            job.setdefault("company_name", company_name)
            return str(company_id)

    # If no existing company found, create one
    created_company = await db_service.create_company({
        "company_name": company_name,
        "normalized_name": normalized_name if await db_service._column_exists('companies', 'normalized_name') else None,
        "company_url": job.get("company_url") or job.get("job_url") or job.get("url") or "",
        "source": "application_auto",
        "is_recruiting_firm": False,
    })
    company_id = created_company.get("company_id") if isinstance(created_company, dict) else None

    if company_id:
        await db_service.update_job(job_id, {
            "company_id": company_id,
            "company_name": company_name,
            "normalized_company": normalized_name,
        })
        job["company_id"] = company_id
        job.setdefault("company_name", company_name)

    return str(company_id) if company_id else None


@router.post("/generate-from-job/{job_id}", response_model=ApplicationResponse)
async def generate_application_from_job(job_id: str, narrative_id: str = None):
    """
    Create application record from reviewed job (Full AI mode).

    Creates application in basic problem analysis stage. User handles AI processing manually.

    Args:
        job_id: UUID of the job to create application for
        narrative_id: UUID of the narrative to use (from UI sidebar selection)

    Returns:
        Application ID and success status
    """

    db_service = get_database_service()
    await db_service.initialize()

    try:
        # 1. Get job and review
        job = await db_service.get_job(job_id)

        if not job:
            raise HTTPException(404, "Job not found")

        await _ensure_job_company(job, job_id, db_service)

        # Get job review for additional context
        review = await db_service.get_job_review(job_id)

        # Get narrative
        async with db_service.pool.acquire() as conn:
            # Use provided narrative_id or fallback to most recent
            if narrative_id:
                narrative = await conn.fetchrow("""
                    SELECT sn.narrative_id, sn.user_id
                    FROM strategic_narratives sn
                    WHERE sn.narrative_id = $1
                    LIMIT 1
                """, UUID(narrative_id))
            else:
                narrative = await conn.fetchrow("""
                    SELECT sn.narrative_id, sn.user_id
                    FROM strategic_narratives sn
                    WHERE sn.user_id IS NOT NULL
                    ORDER BY sn.created_at DESC
                    LIMIT 1
                """)

            if not narrative:
                raise HTTPException(400, "No narrative found. Please create a narrative first.")

            # Get default status - use 'Not Started' for manual AI triggering
            status = await conn.fetchrow("""
                SELECT status_id
                FROM statuses
                WHERE status_name = 'Not Started'
                LIMIT 1
            """)

            if not status:
                status_id = await conn.fetchval("""
                    INSERT INTO statuses (status_name, created_at)
                    VALUES ('Not Started', NOW())
                    RETURNING status_id
                """)
            else:
                status_id = status['status_id']

            # Create application record with properly formatted data
            app_id = await conn.fetchval("""
                INSERT INTO job_applications (
                    company_id,
                    status_id,
                    job_title,
                    job_description,
                    job_link,
                    salary,
                    location,
                    narrative_id,
                    user_id,
                    source_job_id,
                    workflow_mode,
                    keywords,
                    guidance,
                    created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW())
                RETURNING job_application_id
            """,
                job.get('company_id'),
                status_id,
                job.get('title', 'Untitled Position'),
                job.get('description', ''),
                job.get('job_url') or job.get('url', ''),  # Use consistent field naming
                format_job_salary(job),
                format_job_location(job),
                narrative['narrative_id'],
                narrative['user_id'],
                UUID(job_id),
                'ai_generated',
                review.get('keywords') if review else None,
                review.get('guidance') if review else None
            )

        # Update job status
        await db_service.update_job(job_id, {"workflow_status": "ai_approved"})

        logger.info(f"Created application {app_id} for job {job_id} (Full AI mode)")

        return ApplicationResponse(
            success=True,
            application_id=str(app_id),
            message="Application created successfully. You can now add details manually."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create application from job {job_id}: {e}")
        raise HTTPException(500, str(e))


async def _generate_ai_content(
    app_id: str,
    job: Dict,
    company_context: Dict,
    narrative: Dict,
    default_resume: Optional[Dict],
    review: Optional[Dict]
):
    """
    Background task to generate AI content for application.

    Generates:
    - Resume tailoring data (keywords, suggestions, scores)
    - Application message
    - Answers to application questions (if any)

    Updates job_applications record with generated content.
    """
    db_service = get_database_service()

    try:
        logger.info(f"Starting AI content generation for application {app_id}")

        # Initialize AI service
        ai_service = get_application_generator()

        # Extract context data
        job_description = job.get('description', '')
        job_title = job.get('title', 'Untitled Position')
        resume_json = default_resume.get('resume_json', {}) if default_resume else {}
        resume_summary = default_resume.get('summary', '') if default_resume else ''

        # 1. Generate resume tailoring data
        logger.info(f"Generating resume tailoring data for application {app_id}")
        tailoring_data = await ai_service.generate_resume_tailoring_data(
            job_description=job_description,
            full_resume_json=resume_json,
            resume_summary=resume_summary,
            company_context=company_context,
            narrative=narrative,
            job_analysis=review
        )

        # 2. Generate application message
        logger.info(f"Generating application message for application {app_id}")
        application_message = await ai_service.generate_application_message(
            job_title=job_title,
            job_description=job_description,
            company_context=company_context,
            narrative=narrative,
            resume_summary=resume_summary
        )

        # 3. Generate answers to default questions
        logger.info(f"Generating application answers for application {app_id}")
        default_questions = [
            "Why are you interested in this role?",
            "What makes you a strong fit for this position?",
            "What are your salary expectations?",
            "When are you available to start?"
        ]

        application_answers = await ai_service.generate_application_answers(
            questions=default_questions,
            job_title=job_title,
            job_description=job_description,
            company_context=company_context,
            resume_summary=resume_summary
        )

        # 4. Update application record with generated content
        logger.info(f"Updating application {app_id} with AI-generated content")
        async with db_service.pool.acquire() as conn:
            await conn.execute("""
                UPDATE job_applications
                SET tailored_resume_json = $1,
                    application_message = $2,
                    application_questions = $3,
                    updated_at = NOW()
                WHERE job_application_id = $4
            """,
                json.dumps(tailoring_data),
                application_message,
                json.dumps(application_answers),
                UUID(app_id)
            )

        logger.info(f"Successfully completed AI content generation for application {app_id}")

    except Exception as e:
        logger.error(f"Failed to generate AI content for application {app_id}: {e}")
        # Update application with error status
        try:
            async with db_service.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE job_applications
                    SET updated_at = NOW()
                    WHERE job_application_id = $1
                """, UUID(app_id))
        except Exception as update_error:
            logger.error(f"Failed to update application {app_id} after AI error: {update_error}")


@router.post("/create-from-job/{job_id}", response_model=ApplicationResponse)
async def create_application_from_job(job_id: str, mode: str = "fast_track", narrative_id: str = None):
    """
    Create application record from reviewed job (Fast Track mode).

    Creates application and user can immediately start answering questions manually.

    Args:
        job_id: UUID of the job to create application for
        mode: Application mode (fast_track, manual)
        narrative_id: UUID of the narrative to use (from UI sidebar selection)

    Returns:
        Application ID and success status
    """

    db_service = get_database_service()
    await db_service.initialize()

    try:
        job = await db_service.get_job(job_id)

        if not job:
            raise HTTPException(404, "Job not found")

        await _ensure_job_company(job, job_id, db_service)

        # Get narrative
        async with db_service.pool.acquire() as conn:
            # Use provided narrative_id or fallback to most recent
            if narrative_id:
                narrative = await conn.fetchrow("""
                    SELECT sn.narrative_id, sn.user_id
                    FROM strategic_narratives sn
                    WHERE sn.narrative_id = $1
                    LIMIT 1
                """, UUID(narrative_id))
            else:
                narrative = await conn.fetchrow("""
                    SELECT sn.narrative_id, sn.user_id
                    FROM strategic_narratives sn
                    WHERE sn.user_id IS NOT NULL
                    ORDER BY sn.created_at DESC
                    LIMIT 1
                """)

            if not narrative:
                raise HTTPException(400, "No narrative found. Please create a narrative first.")

            # Get default status - use 'Draft' for fast track
            status = await conn.fetchrow("""
                SELECT status_id
                FROM statuses
                WHERE status_name = 'Draft'
                LIMIT 1
            """)

            if not status:
                status_id = await conn.fetchval("""
                    INSERT INTO statuses (status_name, created_at)
                    VALUES ('Draft', NOW())
                    RETURNING status_id
                """)
            else:
                status_id = status['status_id']

            # Create application record with properly formatted data
            app_id = await conn.fetchval("""
                INSERT INTO job_applications (
                    company_id,
                    status_id,
                    job_title,
                    job_description,
                    job_link,
                    salary,
                    location,
                    narrative_id,
                    user_id,
                    source_job_id,
                    workflow_mode,
                    created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
                RETURNING job_application_id
            """,
                job.get('company_id'),
                status_id,
                job.get('title', 'Untitled Position'),
                job.get('description', ''),
                job.get('job_url') or job.get('url', ''),  # Use consistent field naming
                format_job_salary(job),
                format_job_location(job),
                narrative['narrative_id'],
                narrative['user_id'],
                UUID(job_id),
                mode
            )

        # Update job status
        await db_service.update_job(job_id, {"workflow_status": "manual_approved"})

        logger.info(f"Created fast-track application {app_id} for job {job_id}")

        return ApplicationResponse(
            success=True,
            application_id=str(app_id),
            message="Application created successfully. You can now add details manually."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create application from job {job_id}: {e}")
        raise HTTPException(500, str(e))
