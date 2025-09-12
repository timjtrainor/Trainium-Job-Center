def test_generate_company_report_invalid_json(monkeypatch):
    class MockCrew:
        def kickoff(self, inputs):
            return "not json"

    monkeypatch.setattr(
        "app.services.company_service.get_research_company_crew",
        lambda: MockCrew(),
    )

    from app.services.company_service import generate_company_report

    try:
        generate_company_report("SampleCo")
    except ValueError as e:
        assert "Invalid JSON" in str(e)
    else:
        assert False, "ValueError was not raised for invalid JSON"

