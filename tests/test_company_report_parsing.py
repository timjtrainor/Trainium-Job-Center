import json
import sys
from unittest.mock import MagicMock

import pytest


def _sample_report():
    return {
        "company_name": "SampleCo",
        "financial_health": {
            "revenue_trends": "",
            "profitability": "",
            "funding_history": "",
            "investor_information": "",
            "market_performance": "",
            "growth_indicators": "",
            "financial_stability_score": "",
            "key_financial_insights": [],
        },
        "workplace_culture": {
            "company_values": "",
            "employee_satisfaction": "",
            "work_life_balance": "",
            "diversity_inclusion": "",
            "management_style": "",
            "career_support": "",
            "culture_score": "",
            "cultural_highlights": [],
            "potential_concerns": [],
        },
        "leadership_reputation": {
            "executive_team": "",
            "leadership_style": "",
            "industry_reputation": "",
            "media_coverage": "",
            "leadership_stability": "",
            "vision_clarity": "",
            "reputation_score": "",
            "leadership_strengths": [],
            "reputation_risks": [],
        },
        "career_growth": {
            "advancement_opportunities": "",
            "training_programs": "",
            "internal_mobility": "",
            "mentorship_support": "",
            "skill_development": "",
            "promotion_patterns": "",
            "growth_score": "",
            "career_highlights": [],
            "growth_limitations": [],
        },
        "recent_news": {
            "latest_developments": "",
            "press_releases": "",
            "acquisitions_partnerships": "",
            "major_events": "",
            "market_changes": "",
            "recent_announcements": "",
            "news_summary": "",
            "key_updates": [],
        },
        "overall_summary": {
            "recommendation_score": "",
            "key_strengths": [],
            "potential_concerns": [],
            "best_fit_for": "",
            "summary": "",
        },
    }


def _patch_mcp(monkeypatch):
    mock_mcp = MagicMock()
    mock_mcp.types = MagicMock()
    monkeypatch.setitem(sys.modules, "mcp", mock_mcp)
    monkeypatch.setitem(sys.modules, "mcp.types", mock_mcp.types)


def test_generate_company_report_with_commentary_and_braces(monkeypatch):
    _patch_mcp(monkeypatch)
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
    _patch_mcp(monkeypatch)
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
