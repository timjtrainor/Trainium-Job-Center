import sys
from unittest.mock import MagicMock

import pytest


def test_generate_company_report_invalid_json(monkeypatch):
    class MockCrew:
        def kickoff(self, inputs):
            return "````json\n{ invalid: }\n```".replace("````", "```")

    mock_mcp = MagicMock()
    mock_mcp.types = MagicMock()
    monkeypatch.setitem(sys.modules, "mcp", mock_mcp)
    monkeypatch.setitem(sys.modules, "mcp.types", mock_mcp.types)

    monkeypatch.setattr(
        "app.services.company_service.get_research_company_crew", lambda: MockCrew()
    )

    from app.services.company_service import generate_company_report

    with pytest.raises(ValueError) as excinfo:
        generate_company_report("SampleCo")

    assert "Invalid JSON" in str(excinfo.value)

