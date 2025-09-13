import json
import sys
from unittest.mock import MagicMock


def test_company_news(monkeypatch):
    """generate_company_report includes news from mocked DuckDuckGo tool."""

    mock_mcp = MagicMock()
    mock_mcp.types = MagicMock()
    monkeypatch.setitem(sys.modules, "mcp", mock_mcp)
    monkeypatch.setitem(sys.modules, "mcp.types", mock_mcp.types)

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
                    "key_updates": news,
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
    assert report.recent_news.key_updates == [
        "SampleCo announces new product line",
        "SampleCo secures major funding",
    ]
