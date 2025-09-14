"""Integration and formatting tests for JobPostingReviewCrew."""

from typing import Any, Dict
from unittest.mock import patch
import types
import sys
import os

import pytest

# Stub MCP modules before importing crew modules
mcp_stub = types.ModuleType("mcp")
mcp_types_stub = types.ModuleType("mcp.types")
class _ClientSession:
    pass
class _Tool:
    pass
mcp_stub.ClientSession = _ClientSession
mcp_types_stub.Tool = _Tool
sys.modules.setdefault("mcp", mcp_stub)
sys.modules.setdefault("mcp.types", mcp_types_stub)

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from python_service.app.services.crewai.job_posting_review.crew import JobPostingReviewCrew, run_crew
from python_service.app.services.crewai.job_posting_review import _format_crew_result


@pytest.fixture
def sample_job_posting() -> Dict[str, Any]:
    return {
        "title": "Software Engineer",
        "company": "Acme",
        "location": "Remote",
        "description": "Build things",
    }


def test_format_crew_result(sample_job_posting):
    raw = {
        "final": {"recommend": True, "rationale": "Looks good", "confidence": "high"},
        "personas": [{"id": "quick_fit_analyst", "recommend": True, "reason": "strong fit"}],
        "tradeoffs": [],
        "actions": [],
        "sources": [],
    }
    formatted = _format_crew_result(raw, sample_job_posting, "cid-123")
    assert formatted["final"]["recommend"] is True
    assert formatted["personas"][0]["id"] == "quick_fit_analyst"


def test_run_crew_calls_orchestration(sample_job_posting):
    expected = {
        "job_intake": {},
        "pre_filter": {"recommend": True},
        "quick_fit": None,
        "brand_match": None,
    }
    with patch.object(JobPostingReviewCrew, "run_orchestration", return_value=expected) as mocked:
        result = run_crew(sample_job_posting)
        mocked.assert_called_once()
    assert result == expected
