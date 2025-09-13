"""Tests for job posting review response structure."""

import json
import os
import sys
import types
from unittest.mock import Mock, patch


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

from app.services.crewai.job_posting_review.crew import run_crew


def test_run_crew_returns_job_details():
    """run_crew should surface job metadata from crew output."""
    job_posting = {
        "title": "Software Engineer",
        "company": "Acme",
        "location": "Remote",
        "description": "Build things",
    }

    crew_output = {
        "final": {
            "recommend": True,
            "rationale": "Strong match across metrics",
            "confidence": "high",
        },
        "personas": [],
        "job_title": "Software Engineer",
        "company": "Acme",
        "fit_score": 0.9,
    }

    mock_crew = Mock()
    mock_crew.kickoff.return_value = json.dumps(crew_output)

    with patch(
        "app.services.crewai.job_posting_review.crew.get_job_posting_review_crew",
        return_value=mock_crew,
    ):
        result = run_crew(job_posting)

    assert result["data"]["job_title"] == "Software Engineer"
    assert result["data"]["company"] == "Acme"
    assert result["data"]["fit_score"] == 0.9

