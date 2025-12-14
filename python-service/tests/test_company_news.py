import json
import sys
from unittest.mock import MagicMock


def test_company_news(monkeypatch):
    """generate_company_report includes news from mocked DuckDuckGo tool."""

    from app.services.company_service import generate_company_report

    class MockDuckDuckGoTool:
        def search(self, query: str):
            assert query == "SampleCo"
            return [
                "SampleCo announces new product line",
                "SampleCo secures major funding",
            ]

    class MockCrew:
        def kickoff(self, inputs):
            tool = MockDuckDuckGoTool()
            news = tool.search(inputs["company_name"])
            return json.dumps({
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
                    "recent_news": "; ".join(news),
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
            })

    monkeypatch.setattr(
        "app.services.company_service.get_research_company_crew",
        lambda: MockCrew()
    )

    report = generate_company_report("SampleCo")
    assert "SampleCo announces new product line" in report.leadership_reputation.recent_news
    assert "SampleCo secures major funding" in report.leadership_reputation.recent_news
