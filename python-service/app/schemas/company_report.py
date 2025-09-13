from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional


class FinancialHealth(BaseModel):
    """Financial status of a company."""
    revenue: Optional[str] = ""
    profitability: Optional[str] = ""
    funding_status: Optional[str] = ""
    notable_investors: Optional[List[str]] = Field(default_factory=list)


class WorkplaceCulture(BaseModel):
    """Workplace culture aspects."""
    employee_satisfaction: Optional[str] = ""
    work_life_balance: Optional[str] = ""
    benefits: Optional[List[str]] = Field(default_factory=list)


class LeadershipReputation(BaseModel):
    """Leadership reputation details."""
    ceo_rating: Optional[str] = ""
    leadership_changes: Optional[str] = ""
    public_perception: Optional[str] = ""


class CareerGrowth(BaseModel):
    """Career growth opportunities."""
    promotion_opportunities: Optional[str] = ""
    learning_programs: Optional[List[str]] = Field(default_factory=list)
    alumni_success: Optional[str] = ""


class CompanyReport(BaseModel):
    """Comprehensive report about a company."""
    company_name: str
    financial_health: FinancialHealth = Field(default_factory=FinancialHealth)
    workplace_culture: WorkplaceCulture = Field(default_factory=WorkplaceCulture)
    leadership_reputation: LeadershipReputation = Field(default_factory=LeadershipReputation)
    career_growth: CareerGrowth = Field(default_factory=CareerGrowth)
