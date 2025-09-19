"""Tests for PersonaCatalog default model loading."""

from python_service.app.services.persona_loader import PersonaCatalog


def test_models_default_to_env_preference(tmp_path, monkeypatch):
    """Personas without explicit models should use LLM_PREFERENCE order."""
    catalog = tmp_path / "catalog.yaml"
    catalog.write_text(
        """
        group1:
          - id: test
            role: tester
        """
    )

    monkeypatch.setenv(
        "LLM_PREFERENCE", "openai:gpt-5,gemini:gemini-2.5-flash"
    )

    loader = PersonaCatalog(catalog)

    assert loader.get_models("test") == [
        {"provider": "openai", "model": "gpt-5"},
        {"provider": "gemini", "model": "gemini-2.5-flash"},
    ]

