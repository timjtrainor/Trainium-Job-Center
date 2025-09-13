"""
Job Posting models for the Fit Review pipeline.

This module defines the JobPosting model used as input to the
CrewAI-powered job posting fit review process.
"""
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class JobPosting(BaseModel):
    """Model representing a job posting to be evaluated for fit."""
    
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Full job description")
    url: HttpUrl = Field(..., description="URL to the job posting")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Senior Python Developer",
                "company": "Tech Innovations Inc",
                "location": "San Francisco, CA",
                "description": "We are looking for a senior Python developer...",
                "url": "https://example.com/jobs/senior-python-dev"
            }
        }