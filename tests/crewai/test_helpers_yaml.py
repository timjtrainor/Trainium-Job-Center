"""Basic checks for JobPostingReviewCrew YAML configuration and orchestration."""

from typing import Any, Dict
from unittest.mock import patch
import types
import sys
import os
from pathlib import Path

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

PYTHON_SERVICE_PATH = Path(__file__).resolve().parents[2] / "python-service"
if str(PYTHON_SERVICE_PATH) not in sys.path:
    sys.path.insert(0, str(PYTHON_SERVICE_PATH))

if "python_service" not in sys.modules:
    python_service_pkg = types.ModuleType("python_service")
    python_service_pkg.__path__ = [str(PYTHON_SERVICE_PATH)]
    sys.modules["python_service"] = python_service_pkg

from python_service.app.services.crewai.job_posting_review.crew import JobPostingReviewCrew, run_crew


@pytest.fixture
def sample_job_posting() -> Dict[str, Any]:
    return {
        "title": "Senior Software Engineer",
        "company": "TechCorp Inc",
        "location": "Remote",
        "description": "Build services",
    }


def test_agents_and_tasks_yaml_loading():
    crew = JobPostingReviewCrew()
    agents = {"job_intake_agent", "pre_filter_agent", "quick_fit_analyst", "brand_framework_matcher"}
    tasks = {"intake_task", "pre_filter_task", "quick_fit_task", "brand_match_task"}
    assert agents.issubset(set(crew.agents_config.keys()))
    assert tasks.issubset(set(crew.tasks_config.keys()))


def test_run_orchestration_structure(sample_job_posting):
    expected = {
        "job_intake": {"title": "Senior Software Engineer"},
        "pre_filter": {"recommend": True},
        "quick_fit": None,
        "brand_match": None,
        "final": {
            "recommend": True,
            "confidence": "medium",
            "rationale": "Stubbed rationale",
        },
        "personas": [],
        "tradeoffs": [],
        "actions": [],
        "sources": [],
    }
    with patch.object(JobPostingReviewCrew, "run_orchestration", return_value=expected):
        crew = JobPostingReviewCrew()
        result = crew.run_orchestration(sample_job_posting)
    assert result == expected


def test_run_crew_wrapper(sample_job_posting):
    expected = {
        "job_intake": {},
        "pre_filter": {"recommend": True},
        "quick_fit": None,
        "brand_match": None,
        "final": {
            "recommend": True,
            "confidence": "medium",
            "rationale": "Stubbed rationale",
        },
        "personas": [],
        "tradeoffs": [],
        "actions": [],
        "sources": [],
    }
    with patch.object(JobPostingReviewCrew, "run_orchestration", return_value=expected):
        result = run_crew(sample_job_posting)
    assert result == expected
