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
            return json.dumps({"recent_news": news})

    monkeypatch.setattr(
        "app.services.company_service.get_research_company_crew",
        lambda: MockCrew()
    )

    report = generate_company_report("SampleCo")
    assert report["recent_news"] == [
        "SampleCo announces new product line",
        "SampleCo secures major funding",
    ]
