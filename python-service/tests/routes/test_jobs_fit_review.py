from fastapi.testclient import TestClient
from unittest.mock import patch
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

from main import app


def test_fit_review_error_returns_string_message():
    client = TestClient(app)
    job_posting = {
        "title": "Example",
        "company": "ACME",
        "location": "Remote",
        "description": "Desc",
        "url": "http://example.com",
    }

    with patch("app.routes.jobs_fit_review.run_crew", side_effect=Exception("boom")):
        res = client.post(
            "/jobs/posting/fit_review", json={"job_posting": job_posting}
        )

    assert res.status_code == 500
    body = res.json()
    assert body["status"] == "error"
    assert isinstance(body["message"], str)
    assert "fit_review_failed" in body["message"]

