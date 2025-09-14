from python_service.app.schemas.company_report import CompanyReport


def test_company_report_defaults():
    report = CompanyReport(company_name="Test Corp")
    assert report.financial_health.funding_status == ""
    assert report.financial_health.notable_investors == []
    assert report.financial_health.funding_events == []
    assert report.financial_health.risk_factors == []

    assert report.workplace_culture.benefits == []
    assert report.workplace_culture.company_values_emphasized == []
    assert report.workplace_culture.key_culture_signals == []
    assert report.workplace_culture.potential_culture_risks == []

    assert report.leadership_reputation.public_perception == ""
    assert report.leadership_reputation.executive_team_overview == ""
    assert report.leadership_reputation.recent_news_summary == ""
    assert report.leadership_reputation.overall_reputation == ""
    assert (
        report.leadership_reputation.potential_leadership_strengths_to_verify == ""
    )
    assert (
        report.leadership_reputation.potential_reputation_risks_to_verify == ""
    )

    assert report.career_growth.learning_programs == []
    assert report.career_growth.training_and_support == ""
    assert report.career_growth.employee_sentiment_on_growth == ""
    assert report.career_growth.positive_growth_signals == []
    assert report.career_growth.potential_growth_risks == []


def test_company_report_partial_payload():
    payload = {
        "company_name": "Example Inc",
        "financial_health": {"funding_status": "Series A"},
        "career_growth": {"promotion_opportunities": "Fast"},
    }
    report = CompanyReport(**payload)
    assert report.financial_health.funding_status == "Series A"
    # Unprovided fields fall back to defaults
    assert report.financial_health.notable_investors == []
    assert report.financial_health.funding_events == []
    assert report.workplace_culture.company_values_emphasized == []
    assert report.career_growth.learning_programs == []
    assert report.career_growth.positive_growth_signals == []
