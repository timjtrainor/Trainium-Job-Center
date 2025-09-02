import asyncio
from app.services.evaluation_pipeline import evaluate_job


def test_evaluate_job_pipeline():
    job = {"title": "Remote Engineer", "description": "Great remote role with salary"}
    summary = asyncio.run(evaluate_job("1", job, user_id="user-1"))

    # judge decision
    assert summary.decision.final_decision_bool is True
    assert "decision personas approve" in summary.decision.reason_text
    assert 0 <= summary.decision.confidence <= 1

    # motivational and decision personas ran
    ids = {e.persona_id for e in summary.evaluations}
    motivators = {"builder", "maximizer", "harmonizer", "pathfinder", "adventurer"}
    decisions = {"visionary", "realist", "guardian"}
    assert motivators.issubset(ids)
    assert decisions.issubset(ids)

    # advisory delegation produced notes
    motivator_reasons = [e.reason_text for e in summary.evaluations if e.persona_id in motivators]
    assert any("notes" in r for r in motivator_reasons)
