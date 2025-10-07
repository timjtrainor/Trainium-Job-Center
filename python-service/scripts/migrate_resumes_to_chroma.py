"""Utility script to backfill resume data into Chroma collections."""

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

# Ensure the python-service package can be imported when the script runs directly
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.services.chroma_integration_service import ChromaIntegrationService  # noqa: E402

USER_ID = os.getenv("USER_ID", "11111111-2222-3333-4444-555555555555")
RESUME_SELECT_QUERY = (
    "resume_id,resume_name,is_locked,summary_paragraph,summary_bullets,"
    "resume_work_experience(*,resume_accomplishments(*)),"
    "resume_education(*),"
    "resume_certifications(*),"
    "resume_skill_sections(*,resume_skill_items(*))"
)


@dataclass
class ResumeRecord:
    """Container for base resume metadata and hydrated content."""

    base: Dict[str, Any]
    content: Dict[str, Any]


async def fetch_json(client: httpx.AsyncClient, url: str) -> Any:
    """Fetch JSON with error handling."""
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # pragma: no cover - network errors are operational
        logger.error("Request failed for {url}: {error}", url=url, error=str(exc))
        raise


async def fetch_user_profile(client: httpx.AsyncClient, base_url: str) -> Dict[str, Any]:
    """Fetch minimal user profile data to enrich resume text."""
    fields = "first_name,last_name,email,phone_number,city,state,links"
    url = f"{base_url}/users?user_id=eq.{USER_ID}&select={fields}"
    data = await fetch_json(client, url)
    if data:
        return data[0]
    return {}


async def fetch_resumes(client: httpx.AsyncClient, base_url: str) -> List[ResumeRecord]:
    """Fetch resume list then hydrate each with nested relationships."""
    list_url = f"{base_url}/resumes?user_id=eq.{USER_ID}&order=resume_name.asc"
    resume_list = await fetch_json(client, list_url) or []

    records: List[ResumeRecord] = []
    for base_resume in resume_list:
        resume_id = base_resume.get("resume_id")
        if not resume_id:
            continue

        detail_url = (
            f"{base_url}/resumes?resume_id=eq.{resume_id}&user_id=eq.{USER_ID}&select={RESUME_SELECT_QUERY}"
        )
        detail_data = await fetch_json(client, detail_url)
        content = detail_data[0] if detail_data else {}
        records.append(ResumeRecord(base=base_resume, content=content))

    return records


def format_date(date_info: Optional[Dict[str, Any]]) -> str:
    """Render a human-friendly month/year string."""
    if not date_info:
        return ""
    year = date_info.get("year")
    month = date_info.get("month")
    if not year:
        return ""
    if month:
        try:
            return datetime(year, month, 1).strftime("%b %Y")
        except ValueError:  # pragma: no cover - defensive conversion
            return str(year)
    return str(year)


def format_date_range(experience: Dict[str, Any]) -> str:
    """Build a date range label for work experience."""
    start = format_date(experience.get("start_date"))
    end_info = experience.get("end_date")
    is_current = experience.get("is_current")
    end = "Present" if is_current else format_date(end_info)
    if start and end:
        return f"{start} – {end}"
    return start or end or ""


def flatten_keywords(values: Optional[List[Any]]) -> List[str]:
    """Ensure keyword values are consistently strings."""
    if not values:
        return []
    keywords: List[str] = []
    for item in values:
        if isinstance(item, str):
            keywords.append(item)
        elif isinstance(item, dict):
            keywords.extend(str(v) for v in item.values())
        else:
            keywords.append(str(item))
    return [keyword for keyword in {k.strip(): k.strip() for k in keywords if k}.values() if keyword]


def summarise_accomplishment(accomplishment: Dict[str, Any], experience: Dict[str, Any]) -> str:
    """Compose a descriptive text block for an accomplishment."""
    lines: List[str] = []

    description = accomplishment.get("description") or accomplishment.get("original_description")
    if description:
        lines.append(description)

    ai_suggestion = accomplishment.get("ai_suggestion")
    if ai_suggestion:
        lines.append(f"AI Suggestion: {ai_suggestion}")

    keyword_suggestions = flatten_keywords(accomplishment.get("keyword_suggestions"))
    if keyword_suggestions:
        lines.append(f"Keyword Suggestions: {', '.join(keyword_suggestions)}")

    themes = flatten_keywords(accomplishment.get("themes"))
    if themes:
        lines.append(f"Themes: {', '.join(themes)}")

    score = accomplishment.get("score") or accomplishment.get("original_score")
    if isinstance(score, dict) and score:
        score_parts = ", ".join(f"{k}: {v}" for k, v in score.items())
        lines.append(f"Score: {score_parts}")

    role_context = f"Role: {experience.get('job_title', '')} at {experience.get('company_name', '')}".strip()
    if role_context:
        lines.append(role_context)

    return "\n".join(lines).strip()


def build_resume_document(content: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
    """Create a holistic resume document string for vector storage."""
    lines: List[str] = []

    first_name = user_profile.get("first_name")
    last_name = user_profile.get("last_name")
    if first_name or last_name:
        lines.append(f"{first_name or ''} {last_name or ''}".strip())

    contact_bits = [
        user_profile.get("email"),
        user_profile.get("phone_number"),
        ", ".join(filter(None, [user_profile.get("city"), user_profile.get("state")])) or None,
    ]
    contact_line = " | ".join(filter(None, contact_bits))
    if contact_line:
        lines.append(contact_line)

    links = user_profile.get("links") or []
    if links:
        lines.append("Links: " + ", ".join(str(link) for link in links if link))

    summary_paragraph = content.get("summary_paragraph")
    if summary_paragraph:
        lines.append("Summary: " + summary_paragraph)

    summary_bullets = content.get("summary_bullets") or []
    for bullet in summary_bullets:
        lines.append(f"• {bullet}")

    for experience in content.get("resume_work_experience") or []:
        title = experience.get("job_title") or ""
        company = experience.get("company_name") or ""
        location = experience.get("location") or ""
        date_range = format_date_range(experience)
        header_parts = [part for part in [title, company, location, date_range] if part]
        if header_parts:
            lines.append(" | ".join(header_parts))

        for accomplishment in experience.get("resume_accomplishments") or []:
            accomplishment_text = summarise_accomplishment(accomplishment, experience)
            if accomplishment_text:
                lines.append(f"- {accomplishment_text}")

    for section in content.get("resume_skill_sections") or []:
        section_name = section.get("section_name") or "Skills"
        items = section.get("resume_skill_items") or []
        skill_names = [item.get("skill_name") for item in items if item.get("skill_name")]
        if skill_names:
            lines.append(f"{section_name}: {', '.join(skill_names)}")

    for education in content.get("resume_education") or []:
        school = education.get("school") or ""
        degree = education.get("degree") or ""
        majors = education.get("major") or []
        education_line = " | ".join(filter(None, [school, degree, ", ".join(majors)]))
        if education_line:
            lines.append(education_line)

    for cert in content.get("resume_certifications") or []:
        name = cert.get("name")
        if name:
            authority = cert.get("authority")
            issued = cert.get("issue_date")
            lines.append("Certification: " + ", ".join(filter(None, [name, authority, issued])))

    return "\n".join(lines).strip()


async def migrate() -> None:
    """Main migration routine."""
    settings = get_settings()
    base_url = settings.postgrest_url.rstrip("/")

    logger.info("Fetching resume data from PostgREST at {url}", url=base_url)

    async with httpx.AsyncClient(timeout=60.0) as client:
        user_profile = await fetch_user_profile(client, base_url)
        resumes = await fetch_resumes(client, base_url)

    if not resumes:
        logger.warning("No resumes found for migration")
        return

    service = ChromaIntegrationService()
    await service.initialize()

    resume_uploads = 0
    achievement_uploads = 0
    expertise_uploads = 0
    voice_uploads = 0

    for record in resumes:
        resume_id = record.base.get("resume_id")
        resume_name = record.base.get("resume_name", "Resume")
        updated_at = record.base.get("updated_at")

        resume_text = build_resume_document(record.content, user_profile)
        metadata = {
            "resume_id": resume_id,
            "uploaded_from": "migration_script",
        }
        if updated_at:
            metadata["updated_at"] = updated_at

        if resume_text:
            await service.add_resume_document(
                title=resume_name,
                content=resume_text,
                profile_id=USER_ID,
                section="resume",
                additional_metadata=metadata,
            )
            resume_uploads += 1

        for experience in record.content.get("resume_work_experience") or []:
            experience_id = experience.get("resume_work_experience_id") or experience.get("id")
            company_name = experience.get("company_name") or ""
            job_title = experience.get("job_title") or ""
            date_range = format_date_range(experience)
            industry = experience.get("industry") or ""

            normalized_experience_id = experience_id or ChromaIntegrationService.derive_experience_key(
                resume_id=resume_id or "",
                job_title=job_title,
                company_name=company_name,
                date_range=date_range,
            )

            accomplishment_texts: List[str] = []
            accumulated_keywords: List[str] = []

            for accomplishment in experience.get("resume_accomplishments") or []:
                achievement_id = (
                    accomplishment.get("achievement_id")
                    or accomplishment.get("id")
                    or os.urandom(4).hex()
                )
                themes = flatten_keywords(accomplishment.get("themes"))
                accomplishment_text = summarise_accomplishment(accomplishment, experience)
                if not accomplishment_text:
                    continue

                accomplishment_texts.append(accomplishment_text)
                accumulated_keywords.extend(flatten_keywords(accomplishment.get("keyword_suggestions")))

                await service.add_resume_achievement(
                    profile_id=USER_ID,
                    resume_id=resume_id,
                    achievement_id=achievement_id,
                    content=accomplishment_text,
                    job_title=job_title,
                    company_name=company_name,
                    work_experience_id=normalized_experience_id,
                    date_range=date_range,
                    always_include=bool(accomplishment.get("always_include")),
                    order_index=accomplishment.get("order_index"),
                    themes=themes,
                    impact_scope="team" if any("team" in t.lower() for t in themes) else "",
                )
                achievement_uploads += 1

            if accomplishment_texts:
                tone_hint = "metrics-forward" if any(char.isdigit() for text in accomplishment_texts for char in text) else "narrative"
                await service.add_company_voice_pattern(
                    profile_id=USER_ID,
                    resume_id=resume_id,
                    company_name=company_name,
                    job_title=job_title,
                    content="\n".join(accomplishment_texts),
                    industry=industry,
                    tone_hint=tone_hint,
                    keywords=list({kw for kw in accumulated_keywords if kw}),
                    accomplishment_count=len(accomplishment_texts),
                    work_experience_id=normalized_experience_id,
                    additional_metadata={"date_range": date_range} if date_range else None,
                )
                voice_uploads += 1

        summary_paragraph = record.content.get("summary_paragraph") or ""
        summary_bullets = record.content.get("summary_bullets") or []
        summary_text_parts = [summary_paragraph] + summary_bullets
        summary_text = "\n".join(part for part in summary_text_parts if part)
        if summary_text:
            await service.add_user_expertise_document(
                profile_id=USER_ID,
                resume_id=resume_id,
                expertise_area="Executive Summary",
                content=summary_text,
                skills=[],
                seniority="Executive" if "executive" in summary_text.lower() else "",
                source="summary",
            )
            expertise_uploads += 1

        for section in record.content.get("resume_skill_sections") or []:
            section_name = section.get("section_name") or "Skills"
            skills = [item.get("skill_name") for item in section.get("resume_skill_items") or [] if item.get("skill_name")]
            if not skills:
                continue

            section_text = f"{section_name}: {', '.join(skills)}"
            await service.add_user_expertise_document(
                profile_id=USER_ID,
                resume_id=resume_id,
                expertise_area=section_name,
                content=section_text,
                skills=skills,
                source="skills",
            )
            expertise_uploads += 1

    logger.success(
        "Resume migration complete | resumes={resumes} achievements={achievements} expertise={expertise} voice_patterns={voices}",
        resumes=resume_uploads,
        achievements=achievement_uploads,
        expertise=expertise_uploads,
        voices=voice_uploads,
    )


if __name__ == "__main__":
    asyncio.run(migrate())
