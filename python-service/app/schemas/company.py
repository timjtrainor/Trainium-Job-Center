from pydantic import BaseModel


class CompanyRequest(BaseModel):
    company_name: str


class FinancialHealth(BaseModel):
    revenue_trends: str
    profitability: str
    funding_history: str
    investor_information: str
    market_performance: str
    growth_indicators: str
    financial_stability_score: str
    key_financial_insights: list[str]


class WorkplaceCulture(BaseModel):
    company_values: str
    employee_satisfaction: str
    work_life_balance: str
    diversity_inclusion: str
    management_style: str
    career_support: str
    culture_score: str
    cultural_highlights: list[str]
    potential_concerns: list[str]


class LeadershipReputation(BaseModel):
    executive_team: str
    leadership_style: str
    industry_reputation: str
    media_coverage: str
    leadership_stability: str
    vision_clarity: str
    reputation_score: str
    leadership_strengths: list[str]
    reputation_risks: list[str]


class CareerGrowth(BaseModel):
    advancement_opportunities: str
    training_programs: str
    internal_mobility: str
    mentorship_support: str
    skill_development: str
    promotion_patterns: str
    growth_score: str
    career_highlights: list[str]
    growth_limitations: list[str]


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

