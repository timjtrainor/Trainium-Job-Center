from app.schemas.company_report import CompanyReport


def test_company_report_defaults():
    report = CompanyReport(company_name="Test Corp")
    assert report.financial_health.funding_status == ""
    assert report.financial_health.notable_investors == []
    assert report.workplace_culture.benefits == []
    assert report.leadership_reputation.public_perception == ""
    assert report.career_growth.learning_programs == []


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
    assert report.career_growth.learning_programs == []
