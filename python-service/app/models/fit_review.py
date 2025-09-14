"""
Fit Review models for the CrewAI-powered job posting evaluation pipeline.

This module defines the output models for the job posting fit review process,
including persona verdicts, judge decisions, and final review results.
"""
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Enumeration for confidence levels in recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PersonaVerdict(BaseModel):
    """Verdict from a specific persona about a job posting."""
    
    id: str = Field(..., description="Persona identifier")
    recommend: bool = Field(..., description="Whether the persona recommends pursuing this job")
    reason: str = Field(..., description="Primary reasoning for the recommendation")
    notes: Optional[List[str]] = Field(default=None, description="Additional notes or observations")
    sources: Optional[List[str]] = Field(default=None, description="Sources or references used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "technical_leader",
                "recommend": True,
                "reason": "Strong technical challenges and growth opportunities",
                "notes": ["Modern tech stack", "Remote-friendly culture"],
                "sources": ["company_tech_blog", "glassdoor_reviews"]
            }
        }


class FinalRecommendation(BaseModel):
    """Final recommendation from the fit review process."""
    
    recommend: bool = Field(..., description="Final recommendation")
    rationale: str = Field(..., description="Summary rationale for the decision")
    confidence: ConfidenceLevel = Field(..., description="Confidence level in the recommendation")


class FitReviewResult(BaseModel):
    """Complete result of the job posting fit review process."""
    
    job_id: str = Field(..., description="Unique identifier for the job posting")
    final: FinalRecommendation = Field(..., description="Final recommendation and rationale")
    personas: List[PersonaVerdict] = Field(..., description="Individual persona verdicts")
    tradeoffs: Optional[List[str]] = Field(default=None, description="Key tradeoffs identified")
    actions: Optional[List[str]] = Field(default=None, description="Recommended actions to take")
    sources: Optional[List[str]] = Field(default=None, description="Sources consulted during review")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123",
                "final": {
                    "recommend": True,
                    "rationale": "Strong overall fit with minor compensation concerns",
                    "confidence": "high"
                },
                "personas": [
                    {
                        "id": "technical_leader",
                        "recommend": True,
                        "reason": "Excellent technical opportunities"
                    }
                ],
                "tradeoffs": ["Lower salary but better equity potential"],
                "actions": ["Negotiate base salary", "Clarify equity terms"],
                "sources": ["company_website", "glassdoor"]
            }
        }


class JudgeDecision(BaseModel):
    """Decision made by the judge in the fit review process."""
    
    final_recommendation: bool = Field(..., description="Final recommendation from the judge")
    primary_rationale: str = Field(..., description="Primary reasoning for the decision")
    tradeoffs: List[str] = Field(..., description="Key tradeoffs considered")
    decider_confidence: ConfidenceLevel = Field(..., description="Judge's confidence in the decision")
    
    class Config:
        json_schema_extra = {
            "example": {
                "final_recommendation": True,
                "primary_rationale": "Consensus among personas with strong technical alignment",
                "tradeoffs": ["Compensation vs opportunity", "Stability vs growth"],
                "decider_confidence": "high"
            }
        }