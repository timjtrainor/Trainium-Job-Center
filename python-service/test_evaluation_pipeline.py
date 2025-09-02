import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List

from app.services.evaluation_pipeline import EvaluationPipeline


@dataclass
class FakePersona:
    id: str
    decision_lens: str = ""


class FakeCatalog:
    def __init__(self):
        self.groups = {
            "motivational": [
                FakePersona("builder"),
                FakePersona("maximizer"),
                FakePersona("harmonizer"),
                FakePersona("pathfinder"),
                FakePersona("adventurer"),
            ],
            "decision": [
                FakePersona("visionary"),
                FakePersona("realist"),
                FakePersona("guardian"),
            ],
            "judge": [FakePersona("judge")],
            "advisory": [FakePersona("researcher"), FakePersona("headhunter")],
        }

    def get_personas_by_group(self, group: str) -> List[FakePersona]:
        return self.groups.get(group, [])

    def get_default_model(self, persona_id: str) -> Dict[str, str]:
        return {"provider": "fake", "model": "test-model"}


class FakeLLM:
    def advise(
        self,
        advisor_id: str,
        job: Dict[str, Any],
        context: Dict[str, Any] | None = None,
        *,
        provider: str,
        model: str,
    ) -> str:
        return f"{advisor_id} notes"

    def evaluate(
        self,
        persona_id: str,
        decision_lens: str,
        job: Dict[str, Any],
        context: Dict[str, Any] | None = None,
        *,
        provider: str,
        model: str,
    ) -> Dict[str, Any]:
        approve = "remote" in job.get("description", "").lower()
        reason = f"{persona_id} {'approves' if approve else 'rejects'}"
        return {
            "vote": approve,
            "confidence": 0.8 if approve else 0.2,
            "reason": reason,
            "provider": provider,
            "model": model,
        }


class FakeDB:
    initialized = False

    async def insert_persona_evaluation(self, *args, **kwargs):
        return True

    async def insert_decision(self, *args, **kwargs):
        return True

    async def get_user_resume_context(self, user_id: str):
        return {}


def test_evaluate_job_pipeline():
    job = {"title": "Remote Engineer", "description": "Great remote role with salary"}
    pipeline = EvaluationPipeline(FakeCatalog(), FakeLLM(), FakeDB())
    summary = asyncio.run(pipeline.evaluate_job("1", job, user_id="user-1"))

    # judge decision
    assert summary.decision.final_decision_bool is True
    assert "judge" in summary.decision.reason_text
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
