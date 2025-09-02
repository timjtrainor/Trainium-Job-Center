import asyncio
from app.services.evaluation_pipeline import evaluate_job


def test_evaluate_job_pipeline():
    job = {"title": "Remote Engineer", "description": "Great remote role with salary"}
    summary = asyncio.run(evaluate_job("1", job, user_id="user-1"))
    assert summary.decision.final_decision_bool is True
    assert summary.decision.reason_text
    assert 0 <= summary.decision.confidence <= 1
    # ensure motivational personas evaluated
    assert len(summary.evaluations) == 5
    first = summary.evaluations[0]
    assert first.reason_text
    assert 0 <= first.confidence <= 1
