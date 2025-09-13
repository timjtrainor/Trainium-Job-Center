from pydantic import BaseModel, Field
from typing import Union


class CompanyRequest(BaseModel):
    company_name: str


class FinancialHealth(BaseModel):
    funding_events: str = Field(..., alias="funding_status")
    notable_investors: str
    financial_trend: str
    risk_flag: str = Field(..., alias="risk_factors")


class WorkplaceCulture(BaseModel):
    company_values: list[str] = Field(..., alias="company_values_emphasized")
    employee_sentiment: str
    work_life_balance: str
    culture_signals: list[str] = Field(..., alias="key_culture_signals")
    risk_flag: str = Field(..., alias="potential_culture_risks")


class LeadershipReputation(BaseModel):
    executive_team: Union[list[str], str] = Field(..., alias="executive_team_overview")
    recent_news: str = Field(..., alias="recent_news_summary")
    leadership_reputation: str = Field(..., alias="overall_reputation")
    leadership_strengths: Union[list[str], str] = Field(..., alias="potential_leadership_strengths_to_verify")
    reputation_risks: Union[list[str], str] = Field(..., alias="potential_reputation_risks_to_verify")


class CareerGrowth(BaseModel):
    advancement_opportunities: str
    training_support: str = Field(..., alias="training_and_support")
    employee_sentiment: str = Field(..., alias="employee_sentiment_on_growth")
    growth_signals: list[str] = Field(..., alias="positive_growth_signals")
    growth_risks: list[str] = Field(..., alias="potential_growth_risks")


class RecentNews(BaseModel):
    latest_developments: str
    press_releases: str
    acquisitions_partnerships: str
    major_events: str
    market_changes: str
    recent_announcements: str
    news_summary: str
    key_updates: list[str]


class OverallSummary(BaseModel):
    recommendation_score: str
    key_strengths: list[str]
    potential_concerns: list[str]
    best_fit_for: str
    summary: str


class CompanyReport(BaseModel):
    company_name: str
    financial_health: FinancialHealth
    workplace_culture: WorkplaceCulture
    leadership_reputation: LeadershipReputation
    career_growth: CareerGrowth
    #recent_news: RecentNews
    overall_summary: OverallSummary


class CompanyReportResponse(BaseModel):
    report: CompanyReport

