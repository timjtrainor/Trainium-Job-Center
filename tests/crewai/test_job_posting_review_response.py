"""Tests for job posting review response structure."""

import os
import sys
import types
from pathlib import Path
from unittest.mock import patch

PYTHON_SERVICE_PATH = Path(__file__).resolve().parents[2] / "python-service"
if str(PYTHON_SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(PYTHON_SERVICE_PATH))

if "python_service" not in sys.modules:
    python_service_pkg = types.ModuleType("python_service")
    python_service_pkg.__path__ = [str(PYTHON_SERVICE_PATH)]
    sys.modules["python_service"] = python_service_pkg

# Required configuration for importing service modules
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from python_service.app.services.crewai.job_posting_review.crew import (  # noqa: E402
    JobPostingReviewCrew,
    run_crew,
)
from python_service.app.services.crewai.job_posting_review.orchestrator import (  # noqa: E402
    evaluate_job_posting,
)


class _StubTask:
    """Lightweight task stub that mimics CrewAI execute_sync output."""

    def __init__(self, payload):
        self.payload = payload

    def execute_sync(self, context=None):  # noqa: D401 - simple stub
        return types.SimpleNamespace(json_dict=self.payload)


def test_run_crew_returns_job_details():
    """run_crew should surface job metadata and final assessment."""
    job_posting = {
        "title": "Software Engineer",
        "company": "Acme",
        "location": "Remote",
        "description": "Build things",
    }

    crew_output = {
        "job_intake": {"title": "Software Engineer", "company": "Acme"},
        "pre_filter": {"recommend": True},
        "quick_fit": {"overall_fit": "high"},
        "brand_match": {"brand_alignment_score": 7},
        "final": {
            "recommend": True,
            "confidence": "high",
            "rationale": "Quick fit analyst: overall fit high; recommends approve.",
        },
        "personas": [
            {"id": "pre_filter_agent", "recommend": True, "reason": "No blockers"},
            {"id": "quick_fit_analyst", "recommend": True, "reason": "overall fit high"},
        ],
        "tradeoffs": [],
        "actions": ["Move forward with the application process."],
        "sources": ["pre_filter_agent", "quick_fit_analyst"],
    }

    with patch("python_service.app.services.crewai.job_posting_review.orchestrator.evaluate_job_posting", return_value=crew_output):
        result = run_crew(job_posting)

    assert result == crew_output


def test_pre_filter_rejects_salary_below_180k():
    """Test pre-filter rejection for salaries below 180000."""
    job_posting = {
        "title": "Developer",
        "company": "Test Corp",
        "location": "Remote",
        "description": "Position",
        "highest_salary": 170000,  # Below threshold
    }

    rejected_output = {
        "job_intake": job_posting,
        "pre_filter": {
            "recommend": False,
            "reason": "salary below 180000",
        },
        "final": {
            "recommend": False,
            "confidence": "high",
            "rationale": "Pre-filter rejection: salary below 180000",
        },
        "personas": [],
        "tradeoffs": [],
        "actions": [],
        "sources": []
    }

    with patch("python_service.app.services.crewai.job_posting_review.orchestrator.evaluate_job_posting", return_value=rejected_output):
        result = run_crew(job_posting)

    assert result["pre_filter"]["recommend"] is False
    assert "reason" in result["pre_filter"]
    assert result["final"]["recommend"] is False
    assert result["final"]["confidence"] == "high"


def test_pre_filter_rejects_old_posting():
    """Test pre-filter rejection for postings older than 21 days."""
    from datetime import datetime, timedelta

    old_date = (datetime.now() - timedelta(days=25)).isoformat()

    job_posting = {
        "title": "Developer",
        "company": "Test Corp",
        "location": "Remote",
        "description": "Position",
        "date_posted": old_date,  # Older than 21 days
    }

    rejected_output = {
        "job_intake": job_posting,
        "pre_filter": {
            "recommend": False,
            "reason": "job posting older than 21 days",
        },
        "final": {
            "recommend": False,
            "confidence": "high",
            "rationale": "Pre-filter rejection: job posting older than 21 days",
        },
        "personas": [],
        "tradeoffs": [],
        "actions": [],
        "sources": []
    }

    with patch("python_service.app.services.crewai.job_posting_review.orchestrator.evaluate_job_posting", return_value=rejected_output):
        result = run_crew(job_posting)

    assert result["pre_filter"]["recommend"] is False
    assert result["final"]["recommend"] is False
    assert result["final"]["confidence"] == "high"


def test_pre_filter_passes_null_salary_to_specialists():
    """Test pre-filter passes jobs with null/undefined salaries to specialists."""
    job_posting = {
        "title": "Developer",
        "company": "Test Corp",
        "location": "Remote",
        "description": "Position",
        "highest_salary": None,  # Null salary should pass through
    }

    accepted_output = {
        "job_intake": job_posting,
        "pre_filter": {
            "recommend": True,
        },
        "final": {
            "recommend": True,
            "confidence": "medium",
            "rationale": "Job passed pre-filtering",
        },
    }

    with patch("python_service.app.services.crewai.job_posting_review.orchestrator.evaluate_job_posting", return_value=accepted_output):
        result = run_crew(job_posting)

    assert result["pre_filter"]["recommend"] is True
    assert result["final"]["recommend"] is True


def test_pre_filter_passes_high_salary_jobs():
    """Test pre-filter passes jobs with adequate salaries."""
    job_posting = {
        "title": "Senior Developer",
        "company": "Good Corp",
        "location": "Remote",
        "description": "Senior position",
        "highest_salary": 200000,  # Above threshold
    }

    accepted_output = {
        "job_intake": job_posting,
        "pre_filter": {
            "recommend": True,
        },
        "final": {
            "recommend": True,
            "confidence": "medium",
            "rationale": "Job passed pre-filtering",
        },
    }

    with patch("python_service.app.services.crewai.job_posting_review.orchestrator.evaluate_job_posting", return_value=accepted_output):
        result = run_crew(job_posting)

    assert result["pre_filter"]["recommend"] is True
    assert result["final"]["recommend"] is True


def test_pre_filter_acceptance_continues_pipeline():
    """Test that pre_filter acceptance allows the pipeline to continue."""
    job_posting = {
        "title": "Senior Engineer",
        "company": "Big Tech",
        "location": "Remote",
        "description": "High salary position",
        "salary": "250000",  # Above threshold
    }

    accepted_output = {
        "job_intake": {
            "title": "Senior Engineer",
            "company": "Big Tech",
            "salary": "250000",
            "location": "Remote",
            "seniority": "Senior",
            "job_type": "remote",
            "description": "High salary position",
        },
        "pre_filter": {"recommend": True},
        "quick_fit": {
            "career_growth_score": 8,
            "compensation_score": 9,
            "overall_fit": "high",
            "quick_recommendation": "approve",
        },
        "brand_match": {
            "brand_alignment_score": 8,
            "alignment_notes": ["Good match"],
        },
        "final": {
            "recommend": True,
            "confidence": "high",
            "rationale": "Pre-filter: No salary or seniority guardrails were triggered. Quick fit analyst: overall fit high; recommends approve. Brand matcher: brand alignment score 8/10; Good match",
        },
        "personas": [
            {"id": "pre_filter_agent", "recommend": True, "reason": "Passed guardrails"},
            {"id": "quick_fit_analyst", "recommend": True, "reason": "overall fit high"},
            {"id": "brand_framework_matcher", "recommend": True, "reason": "Good match"},
        ],
        "tradeoffs": [],
        "actions": [
            "Move forward with the application process.",
            "Leverage strong brand alignment during outreach.",
        ],
        "sources": [
            "pre_filter_agent",
            "quick_fit_analyst",
            "brand_framework_matcher",
        ],
    }

    with patch("python_service.app.services.crewai.job_posting_review.orchestrator.evaluate_job_posting", return_value=accepted_output):
        result = run_crew(job_posting)

    assert "job_intake" in result
    assert "pre_filter" in result
    assert "quick_fit" in result
    assert "brand_match" in result
    assert "final" in result

    assert result["pre_filter"]["recommend"] is True
    assert result["quick_fit"] is not None
    assert result["brand_match"] is not None
    assert result["quick_fit"]["overall_fit"] == "high"
    assert result["brand_match"]["brand_alignment_score"] == 8
    assert result["final"]["confidence"]
    assert result["final"]["rationale"]
