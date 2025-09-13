import json
import os
from typing import Any, Dict

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.services.crewai.job_posting_review import _format_crew_result


@pytest.fixture
def sample_job_posting() -> Dict[str, Any]:
    return {
        "title": "Software Engineer",
        "company": "Acme Corp",
        "location": "Remote",
        "description": "Build features",
    }


def test_format_crew_result_parses_embedded_json(sample_job_posting):
    verdicts = [
        {"persona_id": "builder", "recommend": True, "reason": "", "notes": [], "sources": []}
    ]
    payload = f"prefix {json.dumps({'motivational_verdicts': verdicts})} suffix"
    formatted = _format_crew_result(payload, sample_job_posting, "test-123")
    assert formatted["final"]["recommend"] is True
    assert formatted["motivational_verdicts"][0]["id"] == "builder"


def test_format_crew_result_errors_without_json(sample_job_posting):
    with pytest.raises(ValueError):
        _format_crew_result("no json here", sample_job_posting, "test-123")


def test_format_crew_result_errors_on_missing_verdicts(sample_job_posting):
    payload = json.dumps({"foo": "bar"})
    with pytest.raises(ValueError):
        _format_crew_result(payload, sample_job_posting, "test-123")
