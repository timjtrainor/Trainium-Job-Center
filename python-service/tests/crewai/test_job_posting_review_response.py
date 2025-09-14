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
        "pre_filter": {"recommend": True},
        "quick_fit": {"overall_fit": "high"},
        "brand_match": {"brand_alignment_score": 7},
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
        "salary": "120000"  # Below threshold
    }

    # Mock the crew output for rejection case
    rejected_output = {
        "job_intake": {
            "title": "Junior Developer",
            "company": "Test Corp", 
            "salary": "120000",
            "location": "Remote",
            "seniority": "Junior",
            "job_type": "remote",
            "description": "Low salary position"
        },
        "pre_filter": {
            "recommend": False,
            "reason": "Rule 1: salary below 180000"
        },
        "quick_fit": None,
        "brand_match": None
    }

    with patch.object(JobPostingReviewCrew, "run_orchestration", return_value=rejected_output):
        result = run_crew(job_posting)

    # Verify the structure
    assert "job_intake" in result
    assert "pre_filter" in result
    assert "quick_fit" in result
    assert "brand_match" in result
    
    # Verify rejection behavior
    assert result["pre_filter"]["recommend"] is False
    assert "reason" in result["pre_filter"]
    
    # Verify early termination - these should be None
    assert result["quick_fit"] is None
    assert result["brand_match"] is None


def test_pre_filter_acceptance_continues_pipeline():
    """Test that pre_filter acceptance allows the pipeline to continue.""" 
    job_posting = {
        "title": "Senior Engineer",
        "company": "Big Tech",
        "location": "Remote", 
        "description": "High salary position",
        "salary": "250000"  # Above threshold
    }

    # Mock the crew output for acceptance case
    accepted_output = {
        "job_intake": {
            "title": "Senior Engineer",
            "company": "Big Tech",
            "salary": "250000", 
            "location": "Remote",
            "seniority": "Senior",
            "job_type": "remote",
            "description": "High salary position"
        },
        "pre_filter": {
            "recommend": True
        },
        "quick_fit": {
            "career_growth_score": 8,
            "compensation_score": 9,
            "overall_fit": "high"
        },
        "brand_match": {
            "brand_alignment_score": 8,
            "alignment_notes": ["Good match"]
        }
    }

    with patch.object(JobPostingReviewCrew, "run_orchestration", return_value=accepted_output):
        result = run_crew(job_posting)

    # Verify the structure
    assert "job_intake" in result
    assert "pre_filter" in result
    assert "quick_fit" in result  
    assert "brand_match" in result
    
    # Verify acceptance behavior
    assert result["pre_filter"]["recommend"] is True
    
    # Verify pipeline continuation - these should NOT be None
    assert result["quick_fit"] is not None
    assert result["brand_match"] is not None
    assert result["quick_fit"]["overall_fit"] == "high"
    assert result["brand_match"]["brand_alignment_score"] == 8

