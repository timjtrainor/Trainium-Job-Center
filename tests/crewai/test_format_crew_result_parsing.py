import json
import os
import types
import sys
from typing import Any, Dict

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

from python_service.app.services.crewai.job_posting_review.crew import _format_crew_result


@pytest.fixture
def sample_job_posting() -> Dict[str, Any]:
    return {
        "title": "Software Engineer",
        "company": "Acme Corp",
        "location": "Remote",
        "description": "Build features",
    }


def test_format_crew_result_parses_embedded_json(sample_job_posting):
    verdicts = [
        {"persona_id": "builder", "recommend": True, "reason": "", "notes": [], "sources": []}
    ]
    payload = f"prefix {json.dumps({'motivational_verdicts': verdicts})} suffix"
    formatted = _format_crew_result(payload, sample_job_posting, "test-123")
    assert formatted["final"]["recommend"] is True
    assert formatted["personas"][0]["id"] == "builder"  # Updated to use personas instead of motivational_verdicts


def test_format_crew_result_errors_without_json(sample_job_posting):
    with pytest.raises(ValueError):
        _format_crew_result("no json here", sample_job_posting, "test-123")


def test_format_crew_result_errors_on_missing_verdicts(sample_job_posting):
    payload = json.dumps({"foo": "bar"})
    with pytest.raises(ValueError):
        _format_crew_result(payload, sample_job_posting, "test-123")


def test_format_crew_result_handles_new_format(sample_job_posting):
    """Test that the new orchestration_task format is handled correctly."""
    new_format_payload = {
        "final": {
            "recommend": False,
            "rationale": "Salary below threshold",
            "confidence": "high"
        },
        "personas": [
            {
                "id": "pre_filter_agent",
                "recommend": False,
                "reason": "Salary too low"
            }
        ],
        "tradeoffs": [],
        "actions": ["Find higher paying jobs"],
        "sources": ["job_posting"]
    }

    formatted = _format_crew_result(new_format_payload, sample_job_posting, "test-456")

    assert formatted["final"]["recommend"] is False
    assert formatted["final"]["rationale"] == "Salary below threshold"
    assert formatted["final"]["confidence"] == "high"
    assert len(formatted["personas"]) == 1
    assert formatted["personas"][0]["id"] == "pre_filter_agent"
    assert formatted["personas"][0]["recommend"] is False
    assert formatted["tradeoffs"] == []
    assert formatted["actions"] == ["Find higher paying jobs"]
    assert formatted["sources"] == ["job_posting"]
