from pydantic import BaseModel, Field, ConfigDict
from typing import Union, List, Optional


class CompanyRequest(BaseModel):
    company_name: str
    company_url: Optional[str] = None
    company_id: Optional[str] = None
    today: Optional[str] = None


class InfoFieldWithSource(BaseModel):
    text: str
    source: Optional[List[str]] = Field(default_factory=list)


class CompanyWebResearchResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    funding_status: Optional[InfoFieldWithSource] = None
    strategic_initiatives: Optional[InfoFieldWithSource] = None
    economic_model: Optional[InfoFieldWithSource] = None
    operating_model: Optional[InfoFieldWithSource] = None
    leadership_pedigree_and_success_mythology: Optional[InfoFieldWithSource] = None
    the_internal_gripes: Optional[InfoFieldWithSource] = None
    talent_bar_expectations: Optional[InfoFieldWithSource] = None
    organizational_headwinds: Optional[InfoFieldWithSource] = None
    cultural_keywords: Optional[InfoFieldWithSource] = None
    core_technical_stack: Optional[InfoFieldWithSource] = None
    market_position: Optional[InfoFieldWithSource] = None
    competitors: Optional[InfoFieldWithSource] = None
    mission: Optional[InfoFieldWithSource] = None
    values: Optional[InfoFieldWithSource] = None
    company_url: Optional[str] = None


# Legacy Models (Keep for backward compatibility during migration if needed)
class FinancialHealth(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    funding_events: str = Field(
        ..., validation_alias="funding_status", serialization_alias="funding_status"
    )
    notable_investors: list[str]
    financial_trend: str
    risk_flag: str = Field(
        ..., validation_alias="risk_factors", serialization_alias="risk_factors"
    )


class WorkplaceCulture(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    company_values: list[str] = Field(
        ..., validation_alias="company_values_emphasized",
        serialization_alias="company_values_emphasized",
    )
    employee_sentiment: str
    work_life_balance: str
    culture_signals: list[str] = Field(
        ..., validation_alias="key_culture_signals",
        serialization_alias="key_culture_signals",
    )
    risk_flag: str = Field(
        ..., validation_alias="potential_culture_risks",
        serialization_alias="potential_culture_risks",
    )


class LeadershipReputation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    executive_team: Union[list[str], str] = Field(
        ..., validation_alias="executive_team_overview",
        serialization_alias="executive_team_overview",
    )
    recent_news: str = Field(
        ..., validation_alias="recent_news_summary",
        serialization_alias="recent_news_summary",
    )
    leadership_reputation: str = Field(
        ..., validation_alias="overall_reputation",
        serialization_alias="overall_reputation",
    )
    leadership_strengths: Union[list[str], str] = Field(
        ..., validation_alias="potential_leadership_strengths_to_verify",
        serialization_alias="potential_leadership_strengths_to_verify",
    )
    reputation_risks: Union[list[str], str] = Field(
        ..., validation_alias="potential_reputation_risks_to_verify",
        serialization_alias="potential_reputation_risks_to_verify",
    )


class CareerGrowth(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    advancement_opportunities: str
    training_support: str = Field(
        ..., validation_alias="training_and_support",
        serialization_alias="training_and_support",
    )
    employee_sentiment: str = Field(
        ..., validation_alias="employee_sentiment_on_growth",
        serialization_alias="employee_sentiment_on_growth",
    )
    growth_signals: list[str] = Field(
        ..., validation_alias="positive_growth_signals",
        serialization_alias="positive_growth_signals",
    )
    growth_risks: list[str] = Field(
        ..., validation_alias="potential_growth_risks",
        serialization_alias="potential_growth_risks",
    )


class OverallSummary(BaseModel):
    recommendation_score: str
    key_strengths: list[str]
    potential_concerns: list[str]
    best_fit_for: str
    summary: str


class CompanyReport(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    company_name: str
    financial_health: FinancialHealth
    workplace_culture: WorkplaceCulture
    leadership_reputation: LeadershipReputation
    career_growth: CareerGrowth
    overall_summary: OverallSummary


class CompanyReportResponse(BaseModel):
    report: CompanyReport
