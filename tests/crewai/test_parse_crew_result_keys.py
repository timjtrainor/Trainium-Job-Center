import json
import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from python_service.app.services.crewai.parser import parse_crew_result


def test_parse_crew_result_requires_mandatory_keys():
    payload = json.dumps({
        "final": {"recommend": True, "rationale": "ok", "confidence": "high"},
        "personas": [],
        "tradeoffs": [],
        "actions": [],
        "fit_score": 0.5
    })
    with pytest.raises(ValueError):
        parse_crew_result(payload)
