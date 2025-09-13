from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class FinancialHealth(BaseModel):
    """Financial status of a company."""

    model_config = ConfigDict(extra="allow")

    revenue: Optional[str] = ""
    profitability: Optional[str] = ""
    funding_status: Optional[str] = ""
    notable_investors: Optional[List[str]] = Field(default_factory=list)
    funding_events: Optional[List[str]] = Field(default_factory=list)
    risk_factors: Optional[List[str]] = Field(default_factory=list)


class WorkplaceCulture(BaseModel):
    """Workplace culture aspects."""

    model_config = ConfigDict(extra="allow")

    employee_satisfaction: Optional[str] = ""
    work_life_balance: Optional[str] = ""
    benefits: Optional[List[str]] = Field(default_factory=list)
    company_values_emphasized: Optional[List[str]] = Field(default_factory=list)
    key_culture_signals: Optional[List[str]] = Field(default_factory=list)
    potential_culture_risks: Optional[List[str]] = Field(default_factory=list)


class LeadershipReputation(BaseModel):
    """Leadership reputation details."""

    model_config = ConfigDict(extra="allow")

    ceo_rating: Optional[str] = ""
    leadership_changes: Optional[str] = ""
    public_perception: Optional[str] = ""
    executive_team_overview: Optional[str] = ""
    recent_news_summary: Optional[str] = ""
    overall_reputation: Optional[str] = ""
    potential_leadership_strengths_to_verify: Optional[str] = ""
    potential_reputation_risks_to_verify: Optional[str] = ""


class CareerGrowth(BaseModel):
    """Career growth opportunities."""

    model_config = ConfigDict(extra="allow")

    promotion_opportunities: Optional[str] = ""
    learning_programs: Optional[List[str]] = Field(default_factory=list)
    alumni_success: Optional[str] = ""
    training_and_support: Optional[str] = ""
    employee_sentiment_on_growth: Optional[str] = ""
    positive_growth_signals: Optional[List[str]] = Field(default_factory=list)
    potential_growth_risks: Optional[List[str]] = Field(default_factory=list)


class CompanyReport(BaseModel):
    """Comprehensive report about a company."""

    model_config = ConfigDict(extra="allow")

    company_name: str
    financial_health: FinancialHealth = Field(default_factory=FinancialHealth)
    workplace_culture: WorkplaceCulture = Field(default_factory=WorkplaceCulture)
    leadership_reputation: LeadershipReputation = Field(default_factory=LeadershipReputation)
    career_growth: CareerGrowth = Field(default_factory=CareerGrowth)
