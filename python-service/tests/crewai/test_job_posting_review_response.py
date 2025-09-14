"""Tests for job posting review response structure."""

import os
import sys
import types
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

# Required configuration for importing service modules
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.services.crewai.job_posting_review.crew import JobPostingReviewCrew, run_crew


def test_run_crew_returns_job_details():
    """run_crew should surface job metadata from crew output."""
    job_posting = {
        "title": "Software Engineer",
        "company": "Acme",
        "location": "Remote",
        "description": "Build things",
    }

    crew_output = {
        "job_intake": {"title": "Software Engineer", "company": "Acme"},
        "pre_filter": {"status": "pass"},
        "quick_fit": {"overall_fit": "high"},
        "brand_match": {"brand_alignment_score": 7},
    }

    with patch.object(JobPostingReviewCrew, "run_orchestration", return_value=crew_output):
        result = run_crew(job_posting)

    assert result == crew_output

