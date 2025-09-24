"""Tests for ChromaDB schemas with enhanced metadata requirements."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.chroma import (
    CareerBrandUpload,
    CareerPathsUpload,
    JobSearchStrategiesUpload,
    ResumeUpload,
    JobPostingUpload,
    CompanyProfileUpload
)


class TestCareerRelatedSchemas:
    """Test suite for career-related upload schemas."""
    
    def test_career_brand_upload_required_fields(self):
        """Test CareerBrandUpload with required fields."""
        data = {
            "title": "My Career Brand",
            "content": "Career brand content",
            "profile_id": "test_profile_123",
            "section": "personal_branding"
        }
        
        upload = CareerBrandUpload(**data)
        
        assert upload.title == "My Career Brand"
        assert upload.content == "Career brand content"
        assert upload.profile_id == "test_profile_123"
        assert upload.section == "personal_branding"
        assert upload.source == ""  # Default value
        assert upload.author == ""  # Default value
        assert isinstance(upload.uploaded_at, datetime)  # Auto-populated
        assert upload.metadata == {}  # Default empty dict
    
    def test_career_brand_upload_missing_required_field(self):
        """Test CareerBrandUpload validation fails when required fields are missing."""
        data = {
            "title": "My Career Brand",
            "content": "Career brand content",
            "profile_id": "test_profile_123"
            # Missing required 'section' field
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CareerBrandUpload(**data)
        
        assert "section" in str(exc_info.value)
    
    def test_career_paths_upload_schema(self):
        """Test CareerPathsUpload schema."""
        data = {
            "title": "Career Path Plan",
            "content": "Career path content",
            "profile_id": "test_profile_123",
            "section": "career_planning",
            "source": "manual_entry",
            "author": "user123"
        }
        
        upload = CareerPathsUpload(**data)
        
        assert upload.title == "Career Path Plan"
        assert upload.section == "career_planning"
        assert upload.source == "manual_entry"
        assert upload.author == "user123"
        assert isinstance(upload.uploaded_at, datetime)
    
    def test_job_search_strategies_upload_schema(self):
        """Test JobSearchStrategiesUpload schema."""
        data = {
            "title": "Networking Strategy",
            "content": "Job search strategy content",
            "profile_id": "test_profile_123",
            "section": "networking"
        }
        
        upload = JobSearchStrategiesUpload(**data)
        
        assert upload.title == "Networking Strategy"
        assert upload.section == "networking"
        assert isinstance(upload.uploaded_at, datetime)
    
    def test_resume_upload_default_section(self):
        """Test ResumeUpload with default section."""
        data = {
            "title": "My Resume",
            "content": "Resume content",
            "profile_id": "test_profile_123"
        }
        
        upload = ResumeUpload(**data)
        
        assert upload.title == "My Resume"
        assert upload.section == "resume"  # Default value
        assert isinstance(upload.uploaded_at, datetime)
    
    def test_resume_upload_custom_section(self):
        """Test ResumeUpload with custom section."""
        data = {
            "title": "Technical Resume",
            "content": "Technical resume content",
            "profile_id": "test_profile_123",
            "section": "technical_resume"
        }
        
        upload = ResumeUpload(**data)
        
        assert upload.section == "technical_resume"


class TestJobPostingAndCompanySchemas:
    """Test suite for job posting and company profile schemas with standard metadata."""
    
    def test_job_posting_upload_required_standard_fields(self):
        """Test JobPostingUpload with required standard metadata fields."""
        data = {
            "title": "Software Engineer",
            "company": "Test Company",
            "description": "Job description",
            "job_id": "job_123",
            "source": "linkedin",
            "status": "active"
        }
        
        upload = JobPostingUpload(**data)
        
        assert upload.title == "Software Engineer"
        assert upload.company == "Test Company"
        assert upload.job_id == "job_123"
        assert upload.source == "linkedin"
        assert upload.status == "active"
        assert isinstance(upload.uploaded_at, datetime)
    
    def test_job_posting_upload_default_status(self):
        """Test JobPostingUpload with default status."""
        data = {
            "title": "Software Engineer",
            "company": "Test Company",
            "description": "Job description",
            "job_id": "job_123",
            "source": "linkedin"
        }
        
        upload = JobPostingUpload(**data)
        
        assert upload.status == "active"  # Default value
    
    def test_job_posting_upload_missing_required_standard_field(self):
        """Test JobPostingUpload validation fails when standard fields are missing."""
        data = {
            "title": "Software Engineer",
            "company": "Test Company",
            "description": "Job description",
            "source": "linkedin"
            # Missing required 'job_id' field
        }
        
        with pytest.raises(ValidationError) as exc_info:
            JobPostingUpload(**data)
        
        assert "job_id" in str(exc_info.value)
    
    def test_company_profile_upload_required_standard_fields(self):
        """Test CompanyProfileUpload with required standard metadata fields."""
        data = {
            "company_name": "Test Company",
            "description": "Company description",
            "industry": "Technology",
            "company_id": "company_123",
            "company_stage": "growth"
        }
        
        upload = CompanyProfileUpload(**data)
        
        assert upload.company_name == "Test Company"
        assert upload.industry == "Technology"
        assert upload.company_id == "company_123"
        assert upload.company_stage == "growth"
        assert upload.ai_first is False  # Default value
        assert isinstance(upload.uploaded_at, datetime)
    
    def test_company_profile_upload_ai_first_true(self):
        """Test CompanyProfileUpload with ai_first set to True."""
        data = {
            "company_name": "AI Company",
            "description": "AI company description",
            "industry": "AI/ML",
            "company_id": "ai_company_123",
            "company_stage": "startup",
            "ai_first": True
        }
        
        upload = CompanyProfileUpload(**data)
        
        assert upload.ai_first is True
    
    def test_company_profile_upload_missing_required_standard_field(self):
        """Test CompanyProfileUpload validation fails when standard fields are missing."""
        data = {
            "company_name": "Test Company",
            "description": "Company description",
            "industry": "Technology",
            "company_stage": "growth"
            # Missing required 'company_id' field
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CompanyProfileUpload(**data)
        
        assert "company_id" in str(exc_info.value)


class TestMetadataFlexibility:
    """Test suite for metadata flexibility."""
    
    def test_additional_metadata_preserved(self):
        """Test that additional metadata is preserved."""
        data = {
            "title": "My Career Brand",
            "content": "Career brand content",
            "profile_id": "test_profile_123",
            "section": "personal_branding",
            "metadata": {
                "custom_field": "custom_value",
                "tags": ["tag1", "tag2"]
            }
        }
        
        upload = CareerBrandUpload(**data)
        
        assert upload.metadata["custom_field"] == "custom_value"
        assert upload.metadata["tags"] == ["tag1", "tag2"]
    
    def test_flexible_metadata_for_job_posting(self):
        """Test that job posting maintains flexible metadata while enforcing standard fields."""
        data = {
            "title": "Software Engineer",
            "company": "Test Company",
            "description": "Job description",
            "job_id": "job_123",
            "source": "linkedin",
            "metadata": {
                "remote_ok": True,
                "visa_sponsorship": False,
                "custom_tags": ["python", "backend"]
            }
        }
        
        upload = JobPostingUpload(**data)
        
        # Standard fields are enforced at schema level
        assert upload.job_id == "job_123"
        assert upload.source == "linkedin"
        
        # Additional metadata is preserved
        assert upload.metadata["remote_ok"] is True
        assert upload.metadata["visa_sponsorship"] is False
        assert upload.metadata["custom_tags"] == ["python", "backend"]