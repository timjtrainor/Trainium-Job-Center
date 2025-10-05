"""Utility for reapplying structured pre-filter logic to existing job reviews."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from .database import DatabaseService, get_database_service
from ..crewai.job_posting_review.orchestrator import JobPostingOrchestrator
from ..crewai.job_posting_review.rules import generate_job_id, validate_job_posting


@dataclass
class PreFilterViolation:
    """Container for reviews that should have been rejected by the pre-filter."""

    job_id: str
    title: str
    company: str
    reason: str
    salary_max: Optional[float]
    date_posted: Optional[datetime]
    retry_count: int
    existing_review: Dict[str, Any]
    job_posting: Dict[str, Any]
    prefilter_result: Dict[str, Any]
    correlation_id: str


class PreFilterBackfillRunner:
    """Detect and optionally remediate job reviews that bypassed the pre-filter."""

    def __init__(self, db: Optional[DatabaseService] = None):
        self.db = db or get_database_service()
        self.orchestrator = JobPostingOrchestrator()

    async def initialize(self) -> None:
        """Ensure the database pool is ready."""
        if not self.db.initialized:
            await self.db.initialize()

    async def run(self, apply_changes: bool = False, limit: Optional[int] = None) -> Dict[str, Any]:
        """Re-evaluate job reviews and optionally persist the backfill."""
        await self.initialize()

        candidates = await self._fetch_candidate_reviews(limit)
        logger.info("Scanning {count} job review candidates for pre-filter violations", count=len(candidates))

        violations: List[PreFilterViolation] = []
        for row in candidates:
            job_posting = self._build_job_posting(row)
            if not job_posting:
                logger.debug("Skipping job_id={job_id} due to invalid job posting payload", job_id=row["job_id"])
                continue

            try:
                validated = validate_job_posting(job_posting)
            except ValueError as exc:
                logger.warning(
                    "Unable to validate job posting for job_id={job_id}: {error}",
                    job_id=row["job_id"],
                    error=str(exc),
                )
                continue

            prefilter_result = self.orchestrator._apply_structured_pre_filter(validated, job_posting)
            if prefilter_result.get("recommend", True):
                continue

            violation = PreFilterViolation(
                job_id=str(row["job_id"]),
                title=str(row.get("title") or job_posting.get("title") or "Untitled Role"),
                company=str(row.get("company") or job_posting.get("company") or "Unknown Company"),
                reason=prefilter_result.get("reason", "Failed structured pre-filter"),
                salary_max=self._extract_numeric(job_posting.get("highest_salary"))
                or self._extract_numeric(job_posting.get("max_amount")),
                date_posted=row.get("date_posted"),
                retry_count=int(row.get("retry_count") or 0),
                existing_review={
                    "recommend": row.get("recommend"),
                    "confidence": row.get("confidence"),
                    "rationale": row.get("rationale"),
                    "processing_time_seconds": row.get("processing_time_seconds"),
                    "crew_version": row.get("crew_version"),
                    "model_used": row.get("model_used"),
                    "retry_count": int(row.get("retry_count") or 0),
                },
                job_posting=job_posting,
                prefilter_result=prefilter_result,
                correlation_id=str(row["job_id"]),
            )
            violations.append(violation)

        logger.info(
            "Pre-filter flagged {count} reviews that require updates", count=len(violations)
        )

        results: List[Dict[str, Any]] = []
        updated_count = 0
        for violation in violations:
            review_payload = self._build_review_payload(violation)
            if apply_changes:
                success = await self.db.insert_job_review(violation.job_id, review_payload)
                if success:
                    updated_count += 1
                results.append({
                    "job_id": violation.job_id,
                    "title": violation.title,
                    "company": violation.company,
                    "reason": violation.reason,
                    "applied": success,
                })
            else:
                results.append({
                    "job_id": violation.job_id,
                    "title": violation.title,
                    "company": violation.company,
                    "reason": violation.reason,
                    "applied": False,
                })

        return {
            "candidates_scanned": len(candidates),
            "violations": len(violations),
            "updated": updated_count,
            "details": results,
            "applied": bool(apply_changes),
        }

    async def _fetch_candidate_reviews(self, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Load job reviews that were previously recommended without overrides."""
        query = """
            SELECT
                jr.job_id,
                jr.recommend,
                jr.confidence,
                jr.rationale,
                jr.retry_count,
                jr.processing_time_seconds,
                jr.crew_version,
                jr.model_used,
                j.title,
                j.company,
                j.description,
                j.max_amount,
                j.min_amount,
                j.currency,
                j.date_posted,
                j.job_url,
                j.job_type,
                j.location_city,
                j.location_state,
                j.location_country,
                j.is_remote,
                j.source_raw
            FROM public.job_reviews jr
            INNER JOIN public.jobs j ON j.id = jr.job_id
            WHERE jr.override_recommend IS NULL
              AND COALESCE(jr.recommend, TRUE) = TRUE
            ORDER BY jr.updated_at DESC
        """

        params: List[Any] = []
        if limit is not None:
            query += " LIMIT $1"
            params.append(limit)

        if not self.db.pool:
            raise RuntimeError("Database connection pool is not initialized")

        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    def _build_job_posting(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a job posting payload compatible with pre-filter validation."""
        source_raw = row.get("source_raw") or {}
        if isinstance(source_raw, dict):
            job_posting: Dict[str, Any] = dict(source_raw)
        else:
            job_posting = {}

        title = row.get("title") or job_posting.get("title")
        company = row.get("company") or job_posting.get("company")
        if not title or not company:
            return None

        job_posting["title"] = str(title)
        job_posting["company"] = str(company)
        job_posting["description"] = row.get("description") or job_posting.get("description") or ""
        job_posting["link"] = row.get("job_url") or job_posting.get("link")

        location_parts = [
            row.get("location_city"),
            row.get("location_state"),
            row.get("location_country"),
        ]
        location = ", ".join([part for part in location_parts if part])
        if not location and row.get("is_remote"):
            location = "Remote"
        job_posting["location"] = location or job_posting.get("location") or "Remote"
        job_posting["job_type"] = row.get("job_type") or job_posting.get("job_type")

        max_amount = self._extract_numeric(row.get("max_amount"))
        min_amount = self._extract_numeric(row.get("min_amount"))
        currency = row.get("currency") or job_posting.get("currency")

        salary_block = job_posting.get("salary") if isinstance(job_posting.get("salary"), dict) else {}
        if min_amount is not None:
            salary_block.setdefault("min_amount", min_amount)
        if max_amount is not None:
            salary_block.setdefault("max_amount", max_amount)
        if currency:
            salary_block.setdefault("currency", currency)
        if salary_block:
            job_posting["salary"] = salary_block

        if max_amount is not None:
            job_posting["max_amount"] = max_amount
            job_posting.setdefault("salary_max", max_amount)
            job_posting.setdefault("highest_salary", max_amount)
        if min_amount is not None:
            job_posting.setdefault("lowest_salary", min_amount)

        date_posted = row.get("date_posted")
        if isinstance(date_posted, datetime):
            job_posting["date_posted"] = date_posted.isoformat()
        elif isinstance(job_posting.get("date_posted"), datetime):
            job_posting["date_posted"] = job_posting["date_posted"].isoformat()

        return job_posting

    def _build_review_payload(self, violation: PreFilterViolation) -> Dict[str, Any]:
        """Construct a review payload that mirrors the orchestrator's rejection output."""
        job_identifier = generate_job_id(violation.job_posting)
        prefilter_payload = self.orchestrator._build_pre_filter_rejection_response(
            job_identifier,
            violation.correlation_id,
            violation.job_posting,
            violation.prefilter_result,
        )

        prefilter_payload.setdefault("metadata", {}).update(
            {
                "source": "pre_filter_backfill",
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "original_recommend": violation.existing_review.get("recommend"),
            }
        )

        final_section = prefilter_payload.get("final", {})
        review_data = {
            "recommend": False,
            "confidence": final_section.get("confidence", "high"),
            "rationale": final_section.get("rationale", violation.reason),
            "personas": [],
            "tradeoffs": [],
            "actions": [],
            "sources": [],
            "overall_alignment_score": prefilter_payload.get("overall_alignment_score", 0),
            "tldr_summary": prefilter_payload.get("tldr_summary"),
            "crew_output": prefilter_payload,
            "processing_time_seconds": violation.existing_review.get("processing_time_seconds") or 0,
            "crew_version": "pre_filter_backfill_v1",
            "model_used": violation.existing_review.get("model_used") or "pre_filter_backfill",
            "retry_count": violation.existing_review.get("retry_count", 0),
            "error_message": None,
        }

        return review_data

    @staticmethod
    def _extract_numeric(value: Any) -> Optional[float]:
        """Safely convert numeric inputs to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


async def run_prefilter_backfill(apply: bool = False, limit: Optional[int] = None) -> Dict[str, Any]:
    """Convenience wrapper used by CLI tools and tests."""
    runner = PreFilterBackfillRunner()
    return await runner.run(apply_changes=apply, limit=limit)
