import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import pytest

from app.services.evaluation_pipeline import EvaluationPipeline
from app.services.persona_llm import PersonaLLM


MOTIVATORS = {"builder", "maximizer", "harmonizer", "pathfinder", "adventurer"}
DECISIONS = {"visionary", "realist", "guardian"}
ADVISORS = {"researcher", "headhunter"}


@dataclass
class FakePersona:
    id: str
    decision_lens: str = ""


class FakeCatalog:
    """Catalog returning provider/model pairs per persona group."""

    def __init__(self, motivator_pair: Tuple[str, str], decision_pair: Tuple[str, str]):
        self.groups = {
            "motivational": [FakePersona(p) for p in MOTIVATORS],
            "decision": [FakePersona(p) for p in DECISIONS],
            "judge": [FakePersona("judge")],
            "advisory": [FakePersona(p) for p in ADVISORS],
        }
        self.motivator_pair = motivator_pair
        self.decision_pair = decision_pair

    def get_personas_by_group(self, group: str) -> List[FakePersona]:
        return self.groups.get(group, [])

    def get_default_model(self, persona_id: str) -> Dict[str, str]:
        if persona_id in MOTIVATORS or persona_id in ADVISORS:
            provider, model = self.motivator_pair
        else:
            provider, model = self.decision_pair
        return {"provider": provider, "model": model}


class RecordingDB:
    """Fake DB capturing evaluations to verify persistence."""

    initialized = True

    def __init__(self) -> None:
        self.saved: List[Any] = []

    async def insert_persona_evaluation(self, evaluation, *args, **kwargs):
        self.saved.append(evaluation)
        return True

    async def insert_decision(self, *args, **kwargs):  # pragma: no cover - trivial
        return True

    async def get_user_resume_context(self, user_id: str):  # pragma: no cover - trivial
        return {}


@pytest.mark.parametrize(
    "motivator_pair, decision_pair",
    [
        (("gemini", "gemini-pro"), ("ollama", "gemma3:1b")),
        (("ollama", "gemma3:1b"), ("openai", "gpt-4o-mini")),
    ],
)
def test_evaluate_job_pipeline_routes_clients(motivator_pair, decision_pair, monkeypatch):
    """Pipeline uses correct clients and persists provider/model."""

    calls: List[Tuple[str, str, str]] = []

    def fake_factory(provider: str, model: str):
        class Client:
            def generate(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
                persona = prompt.split()[0]
                calls.append((provider, model, persona))
                return ""

        return Client()

    monkeypatch.setattr(
        "app.services.persona_llm.create_llm_client", fake_factory
    )

    db = RecordingDB()
    catalog = FakeCatalog(motivator_pair, decision_pair)
    pipeline = EvaluationPipeline(catalog, PersonaLLM(), db)

    job = {"title": "Remote Engineer", "description": "Great remote role with salary"}
    summary = asyncio.run(pipeline.evaluate_job("1", job, user_id="user-1"))

    # provider/model persisted in returned evaluations
    for eval in summary.evaluations:
        expected = motivator_pair if eval.persona_id in MOTIVATORS else decision_pair
        assert (eval.provider, eval.model) == expected

    # provider/model persisted in DB records
    for saved in db.saved:
        expected = motivator_pair if saved.persona_id in MOTIVATORS else decision_pair
        assert (saved.provider, saved.model) == expected

    # ensure each persona used correct client
    for provider, model, persona in calls:
        expected = (
            motivator_pair
            if persona in MOTIVATORS or persona in ADVISORS
            else decision_pair
        )
        assert (provider, model) == expected

    # basic sanity checks retained from original test
    ids = {e.persona_id for e in summary.evaluations}
    assert MOTIVATORS.issubset(ids)
    assert DECISIONS.issubset(ids)

