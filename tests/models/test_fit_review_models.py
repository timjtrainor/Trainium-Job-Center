"""
Unit tests for job posting fit review models.

Tests model validation, serialization, and basic functionality
for the fit review pipeline Pydantic models.
"""
import pytest
from pydantic import ValidationError

from app.models.job_posting import JobPosting
from app.models.fit_review import (
    PersonaVerdict,
    FitReviewResult, 
    JudgeDecision,
    ConfidenceLevel,
    FinalRecommendation,
)


class TestJobPosting:
    """Test JobPosting model validation and functionality."""
    
    def test_valid_job_posting(self):
        """Test creating a valid job posting."""
        job = JobPosting(
            title="Senior Python Developer",
            company="Tech Corp",
            location="San Francisco, CA",
            description="We are looking for a senior Python developer...",
            url="https://example.com/jobs/123"
        )
        
        assert job.title == "Senior Python Developer"
        assert job.company == "Tech Corp"
        assert job.location == "San Francisco, CA"
        assert str(job.url) == "https://example.com/jobs/123"
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise validation errors."""
        with pytest.raises(ValidationError):
            JobPosting(
                title="Developer",
                company="Tech Corp",
                # missing location, description, url
            )
    
    def test_invalid_url(self):
        """Test that invalid URLs raise validation errors."""
        with pytest.raises(ValidationError):
            JobPosting(
                title="Developer",
                company="Tech Corp", 
                location="NYC",
                description="Job description",
                url="not-a-valid-url"
            )


class TestPersonaVerdict:
    """Test PersonaVerdict model validation and functionality."""
    
    def test_valid_persona_verdict(self):
        """Test creating a valid persona verdict."""
        verdict = PersonaVerdict(
            id="technical_leader",
            recommend=True,
            reason="Strong technical challenges and growth opportunities"
        )
        
        assert verdict.id == "technical_leader"
        assert verdict.recommend is True
        assert "technical challenges" in verdict.reason
        assert verdict.notes is None
        assert verdict.sources is None
    
    def test_persona_verdict_with_optional_fields(self):
        """Test persona verdict with notes and sources."""
        verdict = PersonaVerdict(
            id="data_analyst",
            recommend=False,
            reason="Limited data infrastructure",
            notes=["No mention of analytics tools", "Small data team"],
            sources=["job_description", "company_website"]
        )
        
        assert len(verdict.notes) == 2
        assert len(verdict.sources) == 2


class TestFinalRecommendation:
    """Test FinalRecommendation model validation."""
    
    def test_valid_final_recommendation(self):
        """Test creating a valid final recommendation."""
        final = FinalRecommendation(
            recommend=True,
            rationale="Strong overall fit with minor concerns",
            confidence=ConfidenceLevel.HIGH
        )
        
        assert final.recommend is True
        assert final.confidence == ConfidenceLevel.HIGH


class TestFitReviewResult:
    """Test FitReviewResult model validation and functionality."""
    
    def test_valid_fit_review_result(self):
        """Test creating a valid fit review result."""
        final = FinalRecommendation(
            recommend=True,
            rationale="Good technical fit",
            confidence=ConfidenceLevel.MEDIUM
        )
        
        verdict = PersonaVerdict(
            id="strategist",
            recommend=True,
            reason="Aligns with career goals"
        )
        
        result = FitReviewResult(
            job_id="job_123",
            final=final,
            personas=[verdict]
        )
        
        assert result.job_id == "job_123"
        assert result.final.recommend is True
        assert len(result.personas) == 1
        assert result.tradeoffs is None
        assert result.actions is None


class TestJudgeDecision:
    """Test JudgeDecision model validation."""
    
    def test_valid_judge_decision(self):
        """Test creating a valid judge decision."""
        decision = JudgeDecision(
            final_recommendation=True,
            primary_rationale="Consensus among personas",
            tradeoffs=["Compensation vs opportunity"],
            decider_confidence=ConfidenceLevel.HIGH
        )
        
        assert decision.final_recommendation is True
        assert len(decision.tradeoffs) == 1
        assert decision.decider_confidence == ConfidenceLevel.HIGH


class TestConfidenceLevel:
    """Test ConfidenceLevel enum."""
    
    def test_confidence_level_values(self):
        """Test that confidence level enum has expected values."""
        assert ConfidenceLevel.LOW == "low"
        assert ConfidenceLevel.MEDIUM == "medium"
        assert ConfidenceLevel.HIGH == "high"
    
    def test_confidence_level_in_model(self):
        """Test using confidence level in a model."""
        final = FinalRecommendation(
            recommend=False,
            rationale="Too many red flags",
            confidence=ConfidenceLevel.LOW
        )
        
        assert final.confidence == ConfidenceLevel.LOW