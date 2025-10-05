"""LinkedIn job import endpoints with duplicate detection and error handling."""

import asyncio
import re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from loguru import logger

from ....services.crewai.linkedin_recommended_jobs.crew import LinkedInRecommendedJobsCrew
from ....services.infrastructure.database import get_database_service
from ....services.infrastructure.job_review_service import JobReviewService
from ....services.infrastructure.company_normalization import normalize_company_name

router = APIRouter(prefix="/linkedin-jobs", tags=["LinkedIn Jobs"])


class LinkedInJobUrlRequest(BaseModel):
    url: str = Field(..., description="LinkedIn job posting URL")

    @validator('url')
    def validate_linkedin_url(cls, v):
        if not v.startswith('https://www.linkedin.com/jobs/view/'):
            raise ValueError('Must be a valid LinkedIn job URL')
        return v


class JobFetchResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    message: str
    error: Optional[str] = None
    existing_job_id: Optional[str] = None
    status: Optional[str] = None
    task_id: Optional[str] = None


class LinkedInAuthError(Exception):
    """Raised when LinkedIn authentication fails."""
    pass


class LinkedInRateLimitError(Exception):
    """Raised when LinkedIn rate limit is hit."""
    pass


@router.post("/fetch-by-url", response_model=JobFetchResponse)
async def fetch_linkedin_job_by_url(
    request: LinkedInJobUrlRequest,
    background_tasks: BackgroundTasks
):
    """
    Fetch LinkedIn job by URL with duplicate detection and error handling.

    Flow:
    1. Check for duplicates by URL
    2. Fetch job details via LinkedIn MCP
    3. Check for duplicates by normalized company+title
    4. Auto-match or create company
    5. Insert job with 'pending_review' status
    6. Queue for AI review in background
    7. Return immediately with task tracking
    """

    db_service = get_database_service()
    await db_service.initialize()

    try:
        # 1. DUPLICATE DETECTION - Check by URL first
        existing_by_url = await db_service.get_job_by_url(request.url)

        if existing_by_url:
            return JobFetchResponse(
                success=False,
                error="duplicate",
                message=_get_duplicate_message(existing_by_url.get('workflow_status')),
                existing_job_id=str(existing_by_url.get('id')),
                status=existing_by_url.get('workflow_status')
            )

        # 2. FETCH FROM LINKEDIN MCP with error handling
        try:
            job_data = await _fetch_job_via_mcp(request.url)
        except LinkedInAuthError as e:
            logger.error(f"LinkedIn authentication failed: {e}")
            return JobFetchResponse(
                success=False,
                error="auth_expired",
                message="LinkedIn session expired. Please update your li_at cookie in settings."
            )
        except LinkedInRateLimitError as e:
            logger.warning(f"LinkedIn rate limit hit: {e}")
            return JobFetchResponse(
                success=False,
                error="rate_limit",
                message="LinkedIn rate limit reached. Try again in 15 minutes.",
            )
        except Exception as e:
            logger.error(f"LinkedIn MCP fetch failed: {e}")
            return JobFetchResponse(
                success=False,
                error="fetch_failed",
                message=f"Couldn't fetch job details: {str(e)}. Try pasting details manually."
            )

        # 3. DUPLICATE DETECTION - Check by normalized company + title
        normalized_company = normalize_company_name(job_data.get('company', ''))
        normalized_title = _normalize_job_title(job_data.get('title', ''))

        existing_by_content = await db_service.get_job_by_normalized_fields(
            normalized_company=normalized_company,
            normalized_title=normalized_title
        )

        if existing_by_content:
            return JobFetchResponse(
                success=False,
                error="duplicate",
                message=f"Similar job already exists: '{existing_by_content.get('title')}' at {existing_by_content.get('company_name')}",
                existing_job_id=str(existing_by_content.get('id')),
                status=existing_by_content.get('workflow_status')
            )

        # 4. AUTO COMPANY MATCHING
        company_id = await _match_or_create_company(job_data.get('company', ''), job_data)

        # 5. INSERT JOB
        job_record = {
            "title": job_data.get('title'),
            "company_id": company_id,
            "company_name": job_data.get('company'),
            "location": job_data.get('location'),
            "description": job_data.get('description'),
            "url": request.url,
            "source": "linkedin_manual",
            "workflow_status": "pending_review",
            "date_posted": job_data.get('posted_date'),
            "salary_min": job_data.get('salary_min'),
            "salary_max": job_data.get('salary_max'),
            "scraped_at": datetime.utcnow().isoformat(),
            "normalized_title": normalized_title,
            "normalized_company": normalized_company
        }

        job_id = await db_service.insert_job(job_record)

        # 6. QUEUE FOR REVIEW in background
        background_tasks.add_task(_queue_job_for_review, str(job_id))

        logger.info(f"LinkedIn job fetched successfully: {job_id}")

        return JobFetchResponse(
            success=True,
            job_id=str(job_id),
            message="Job fetched and queued for AI review",
            task_id=str(job_id)  # Use for polling status
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching LinkedIn job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _fetch_job_via_mcp(url: str) -> dict:
    """Fetch job details from LinkedIn using MCP tool."""
    crew = LinkedInRecommendedJobsCrew()

    try:
        mcp_tools = crew._get_mcp_tools()

        job_details_tool = next(
            (t for t in mcp_tools if t.name == 'get_job_details'),
            None
        )

        if not job_details_tool:
            raise Exception("LinkedIn MCP tool 'get_job_details' not available")

        # Call the MCP tool
        # The tool's run() method is synchronous but internally uses async calls
        # We need to run it in an executor to avoid blocking the event loop
        import asyncio
        import concurrent.futures

        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                lambda: job_details_tool.run(url=url)
            )

        # Validate required fields
        if not result.get('title') or not result.get('company'):
            raise Exception("Incomplete job data from LinkedIn")

        return result

    except Exception as e:
        # Check if it's an auth error
        if 'authentication' in str(e).lower() or 'unauthorized' in str(e).lower():
            raise LinkedInAuthError(str(e))
        # Check if it's a rate limit
        if 'rate limit' in str(e).lower() or 'too many requests' in str(e).lower():
            raise LinkedInRateLimitError(str(e))
        raise

    finally:
        crew.close()


async def _match_or_create_company(company_name: str, job_data: dict) -> str:
    """Match existing company or auto-create new one with LinkedIn data."""
    db_service = get_database_service()

    # Normalize company name
    normalized_name = normalize_company_name(company_name)

    # Check for existing company
    existing = await db_service.get_company_by_normalized_name(normalized_name)

    if existing:
        logger.info(f"Matched to existing company: {existing.get('company_name')}")
        return str(existing.get('company_id'))

    # Create new company
    new_company = await db_service.create_company({
        "company_name": company_name,
        "normalized_name": normalized_name,
        "company_url": _extract_company_url_from_job_url(job_data.get('url', '')),
        "source": "linkedin_auto",
        "is_recruiting_firm": False
    })

    company_id = new_company.get('company_id') if isinstance(new_company, dict) else new_company.company_id

    logger.info(f"Created new company: {company_name} -> {company_id}")

    # Optional: Enrich with LinkedIn company profile (don't fail if it errors)
    try:
        await _enrich_company_from_linkedin(str(company_id), company_name)
    except Exception as e:
        logger.warning(f"Company enrichment failed: {e}")

    return str(company_id)


async def _enrich_company_from_linkedin(company_id: str, company_name: str):
    """Optionally fetch LinkedIn company profile to enrich data."""
    crew = LinkedInRecommendedJobsCrew()

    try:
        mcp_tools = crew._get_mcp_tools()
        company_tool = next(
            (t for t in mcp_tools if t.name == 'get_company_profile'),
            None
        )

        if company_tool:
            profile = company_tool.run(company_name=company_name)

            db_service = get_database_service()
            await db_service.update_company(company_id, {
                "mission": {"text": profile.get("about", "")},
                "employee_count": profile.get("size"),
                "industry": profile.get("industry")
            })

    finally:
        crew.close()


async def _queue_job_for_review(job_id: str):
    """Queue job for AI review (runs in background)."""
    try:
        review_service = JobReviewService()
        await review_service.initialize()
        await review_service.queue_single_job(job_id)
    except Exception as e:
        logger.error(f"Failed to queue job {job_id} for review: {e}")


def _get_duplicate_message(status: str) -> str:
    """Get user-friendly message for duplicate jobs."""
    messages = {
        "rejected": "You already rejected this job",
        "ai_approved": "This job is already in your applications",
        "manual_approved": "This job is already in your applications",
        "pending_review": "This job is already being reviewed"
    }
    return messages.get(status, "This job already exists in the system")


def _normalize_job_title(title: str) -> str:
    """Normalize job title for duplicate detection."""
    # Remove common variations
    normalized = re.sub(r'\b(senior|sr|junior|jr|mid|level|i|ii|iii)\b', '', title.lower())
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return ' '.join(normalized.split())  # Remove extra whitespace


def _extract_company_url_from_job_url(job_url: str) -> str:
    """Extract company LinkedIn URL from job posting URL."""
    # LinkedIn job URLs often contain company info
    match = re.search(r'company=([^&]+)', job_url)
    if match:
        return f"https://www.linkedin.com/company/{match.group(1)}"
    return ""


@router.get("/review-status/{job_id}")
async def get_review_status(job_id: str):
    """Check if job review is complete (for polling)."""
    db_service = get_database_service()
    await db_service.initialize()

    job = await db_service.get_job(job_id)
    review = await db_service.get_job_review(job_id)

    if review:
        return {
            "status": "complete",
            "recommendation": review.get('recommendation'),
            "score": review.get('overall_alignment_score'),
            "confidence": review.get('confidence_level')
        }
    else:
        return {
            "status": "pending",
            "workflow_status": job.get('workflow_status') if job else 'unknown'
        }
