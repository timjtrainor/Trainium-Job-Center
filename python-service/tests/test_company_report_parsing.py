import json
import sys
from unittest.mock import MagicMock

import pytest


def _sample_report():
    return {
        "company_name": "SampleCo",
        "financial_health": {
            "funding_events": "",
            "notable_investors": [],
            "financial_trend": "",
            "risk_flag": "",
        },
        "workplace_culture": {
            "company_values": [],
            "employee_sentiment": "",
            "work_life_balance": "",
            "culture_signals": [],
            "risk_flag": "",
        },
        "leadership_reputation": {
            "executive_team": [],
            "recent_news": "",
            "leadership_reputation": "",
            "leadership_strengths": [],
            "reputation_risks": [],
        },
        "career_growth": {
            "advancement_opportunities": "",
            "training_support": "",
            "employee_sentiment": "",
            "growth_signals": [],
            "growth_risks": [],
        },
        "overall_summary": {
            "recommendation_score": "",
            "key_strengths": [],
            "potential_concerns": [],
            "best_fit_for": "",
            "summary": "",
        },
    }


def test_generate_company_report_with_commentary_and_braces(monkeypatch):
    sample_json = json.dumps(_sample_report())
    raw_output = (
        "Intro text with {braces} before JSON.\n"
        f"```json\n{sample_json}\n```\n"
        "Trailing notes with more {braces}."
    )

    class MockCrew:
        def kickoff(self, inputs):
            return raw_output

    monkeypatch.setattr(
        "app.services.company_service.get_research_company_crew", lambda: MockCrew()
    )

    from app.services.company_service import generate_company_report

    report = generate_company_report("SampleCo")
    assert report.company_name == "SampleCo"


def test_generate_company_report_no_json_block(monkeypatch):
    raw_output = "Leading text without any JSON block."

    class MockCrew:
        def kickoff(self, inputs):
            return raw_output

    monkeypatch.setattr(
        "app.services.company_service.get_research_company_crew", lambda: MockCrew()
    )

    from app.services.company_service import generate_company_report

    with pytest.raises(ValueError) as excinfo:
        generate_company_report("SampleCo")
    assert "No JSON" in str(excinfo.value)
