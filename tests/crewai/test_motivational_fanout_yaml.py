"""YAML binding tests for JobPostingReviewCrew."""

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

from python_service.app.services.crewai.job_posting_review.crew import JobPostingReviewCrew


@pytest.fixture
def sample_job_posting() -> Dict[str, Any]:
    return {
        "title": "Backend Developer",
        "company": "Example Corp",
        "location": "Remote",
        "description": "Maintain APIs",
    }


def test_yaml_agent_and_task_binding():
    crew = JobPostingReviewCrew()
    for agent in ["job_intake_agent", "pre_filter_agent", "quick_fit_analyst", "brand_framework_matcher"]:
        assert agent in crew.agents_config
        assert hasattr(crew, agent)
    for task in ["intake_task", "pre_filter_task", "quick_fit_task", "brand_match_task"]:
        assert task in crew.tasks_config
        assert hasattr(crew, task)


def test_run_orchestration_callable(sample_job_posting):
    expected = {
        "job_intake": {},
        "pre_filter": {"recommend": True},
        "quick_fit": None,
        "brand_match": None,
    }
    with patch.object(JobPostingReviewCrew, "run_orchestration", return_value=expected):
        crew = JobPostingReviewCrew()
        result = crew.run_orchestration(sample_job_posting)
    assert result == expected
