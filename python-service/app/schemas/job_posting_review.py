"""Schemas for job posting review operations."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class JobPostingData(BaseModel):
    """Job posting data for review."""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: Optional[str] = Field(None, description="Job location")
    description: str = Field(..., description="Job description text")
    url: Optional[str] = Field(None, description="Job posting URL")
    salary_range: Optional[str] = Field(None, description="Salary range if specified")
    requirements: Optional[List[str]] = Field(None, description="List of key requirements")


class JobPostingReviewRequest(BaseModel):
    """Request schema for job posting review analysis."""
    job_posting: JobPostingData = Field(..., description="Job posting to analyze")
    company_research: Optional[Dict[str, Any]] = Field(None, description="Company research data from research_company crew")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional options for analysis")


class SkillsFit(BaseModel):
    """Skills analysis results."""
    technical_alignment: str
    experience_match: str
    skill_gaps: List[str]
    strengths: List[str]
    seniority_fit: str
    development_opportunities: List[str]
    skills_score: str
    key_insights: List[str]


class CulturalFit(BaseModel):
    """Cultural fit analysis results."""
    values_alignment: str
    work_environment: str
    team_dynamics: str
    management_style: str
    work_life_balance: str
    mission_alignment: str
    culture_score: str
    cultural_highlights: List[str]
    potential_concerns: List[str]


class CompensationFit(BaseModel):
    """Compensation analysis results."""
    base_salary: str
    total_compensation: str
    benefits_package: str
    equity_potential: str
    market_competitiveness: str
    compensation_transparency: str
    compensation_score: str
    market_insights: List[str]
    value_propositions: List[str]


class CareerGrowth(BaseModel):
    """Career growth analysis results."""
    advancement_opportunities: str
    skill_development: str
    leadership_potential: str
    industry_positioning: str
    learning_support: str
    trajectory_alignment: str
    growth_score: str
    career_highlights: List[str]
    growth_limitations: List[str]


class OverallEvaluation(BaseModel):
    """Overall fit evaluation."""
    recommend: bool
    fit_score: str
    confidence_level: str
    rationale: str
    key_strengths: List[str]
    key_concerns: List[str]
    decision_factors: List[str]


class JobPostingReviewResponse(BaseModel):
    """Response schema for job posting review analysis."""
    job_title: str
    company_name: str
    skills_fit: SkillsFit
    cultural_fit: CulturalFit
    compensation_fit: CompensationFit
    career_growth: CareerGrowth
    overall_evaluation: OverallEvaluation
    recommended_actions: List[str]
    questions_to_ask: List[str]
    negotiation_points: List[str]