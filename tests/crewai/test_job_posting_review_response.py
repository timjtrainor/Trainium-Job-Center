"""Tests for job posting review response structure."""

import os
import sys
import types
from pathlib import Path
from unittest.mock import patch


# Stub external dependency imported by crew module
mcp_stub = types.ModuleType("mcp")
mcp_types_stub = types.ModuleType("mcp.types")


class _ClientSession:  # minimal placeholder
    pass


class _Tool:  # placeholder for mcp.types.Tool
    pass


mcp_stub.ClientSession = _ClientSession
mcp_types_stub.Tool = _Tool
sys.modules.setdefault("mcp", mcp_stub)
sys.modules.setdefault("mcp.types", mcp_types_stub)

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

    with patch.object(JobPostingReviewCrew, "run_orchestration", return_value=crew_output):
        result = run_crew(job_posting)

    assert result == crew_output


def test_pre_filter_rejection_terminates_early():
    """Test that pre_filter rejection stops execution and returns proper structure."""
    job_posting = {
        "title": "Junior Developer",
        "company": "Test Corp",
        "location": "Remote",
        "description": "Low salary position",
        "salary": "120000",  # Below threshold
    }

    rejected_output = {
        "job_intake": {
            "title": "Junior Developer",
            "company": "Test Corp",
            "salary": "120000",
            "location": "Remote",
            "seniority": "Junior",
            "job_type": "remote",
            "description": "Low salary position",
        },
        "pre_filter": {
            "recommend": False,
            "reason": "Rule 1: salary below 180000",
        },
        "quick_fit": None,
        "brand_match": None,
        "final": {
            "recommend": False,
            "confidence": "high",
            "rationale": "Pre-filter rejection: Rule 1: salary below 180000",
        },
        "personas": [
            {
                "id": "pre_filter_agent",
                "recommend": False,
                "reason": "Rule 1: salary below 180000",
            }
        ],
        "tradeoffs": ["Compensation does not meet minimum salary requirements."],
        "actions": ["Target roles with stronger compensation before applying."],
        "sources": ["pre_filter_agent"],
    }

    with patch.object(JobPostingReviewCrew, "run_orchestration", return_value=rejected_output):
        result = run_crew(job_posting)

    assert "job_intake" in result
    assert "pre_filter" in result
    assert "quick_fit" in result
    assert "brand_match" in result
    assert "final" in result

    assert result["pre_filter"]["recommend"] is False
    assert "reason" in result["pre_filter"]

    assert result["quick_fit"] is None
    assert result["brand_match"] is None
    assert result["final"]["confidence"] == "high"
    assert "Rule 1" in result["final"]["rationale"]


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

    with patch.object(JobPostingReviewCrew, "run_orchestration", return_value=accepted_output):
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


def test_run_orchestration_generates_final_summary_for_acceptance():
    """run_orchestration should synthesize persona outputs into a final block."""

    crew = JobPostingReviewCrew()
    job_posting = {
        "title": "Staff Engineer",
        "company": "Growth Labs",
        "description": "Help scale platform",
    }

    intake_payload = {"title": "Staff Engineer", "company": "Growth Labs"}
    pre_payload = {"recommend": True, "reason": "Salary clears guardrails"}
    quick_payload = {
        "overall_fit": "medium",
        "quick_recommendation": "approve",
        "compensation_score": 6,
    }
    brand_payload = {
        "brand_alignment_score": 8,
        "alignment_notes": ["Strong mission fit", "Clarify team structure"],
    }

    stub_crew = types.SimpleNamespace(
        tasks=[
            _StubTask(intake_payload),
            _StubTask(pre_payload),
            _StubTask(quick_payload),
            _StubTask(brand_payload),
        ]
    )

    with patch.object(JobPostingReviewCrew, "crew", return_value=stub_crew):
        result = crew.run_orchestration(job_posting)

    final = result["final"]
    assert final["recommend"] is True
    assert final["confidence"] in {"medium", "high"}
    assert "Quick fit analyst" in final["rationale"]
    assert any(p["id"] == "brand_framework_matcher" for p in result["personas"])
    assert "Clarify team structure" in result["tradeoffs"]
    assert any("Leverage strong brand alignment" in action for action in result["actions"])
    assert "pre_filter_agent" in result["sources"]


def test_run_orchestration_generates_final_summary_for_rejection():
    """Pre-filter rejection should return final block with high confidence."""

    crew = JobPostingReviewCrew()
    job_posting = {"title": "Junior Developer"}

    intake_payload = {"title": "Junior Developer", "company": "Test Corp"}
    pre_payload = {"recommend": False, "reason": "Rule 1: salary below 180000"}

    stub_crew = types.SimpleNamespace(
        tasks=[
            _StubTask(intake_payload),
            _StubTask(pre_payload),
            _StubTask({}),
            _StubTask({}),
        ]
    )

    with patch.object(JobPostingReviewCrew, "crew", return_value=stub_crew):
        result = crew.run_orchestration(job_posting)

    final = result["final"]
    assert final["recommend"] is False
    assert final["confidence"] == "high"
    assert "Rule 1" in final["rationale"]
    assert result["quick_fit"] is None
    assert result["brand_match"] is None
    assert result["actions"]
