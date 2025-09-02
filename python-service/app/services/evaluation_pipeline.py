"""Crew-based job evaluation pipeline orchestrating personas."""
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List
from loguru import logger

from ..models.evaluations import PersonaEvaluation, Decision, EvaluationSummary
from .persona_loader import PersonaCatalog
from .persona_llm import PersonaLLM
try:
    from .database import get_database_service
except Exception:  # pragma: no cover - fallback when asyncpg missing
    class _DummyDB:
        initialized = False
        async def insert_persona_evaluation(self, *_, **__):
            return False
        async def insert_decision(self, *_, **__):
            return False

    def get_database_service() -> _DummyDB:  # type: ignore
        return _DummyDB()


_catalog = PersonaCatalog(Path(__file__).with_name("persona_catalog.yaml"))
_llm = PersonaLLM()
_db = get_database_service()


@dataclass
class Task:
    """Simple async task wrapper."""
    name: str
    coro: Callable[[], Awaitable[Any]]

    async def run(self) -> Any:
        return await self.coro()


class Crew:
    """Sequential executor for persona tasks."""

    def __init__(self, tasks: List[Task]):
        self.tasks = tasks

    async def run(self) -> List[Any]:
        results: List[Any] = []
        for task in self.tasks:
            results.append(await task.run())
        return results


async def evaluate_job(job_id: str, job: Dict[str, Any], user_id: str) -> EvaluationSummary:
    """Evaluate a job using a crew of motivational, decision, and judge personas."""
    logger.info(f"Starting evaluation for job {job_id}")
    resume_context: Dict[str, Any] = {}
    if _db.initialized and user_id:
        try:
            resume_context = await _db.get_user_resume_context(user_id)
        except Exception as e:
            logger.error(f"Failed to load resume context: {e}")

    all_evals: List[PersonaEvaluation] = []
    motivator_evals: List[PersonaEvaluation] = []
    decision_evals: List[PersonaEvaluation] = []
    final_decision: Decision | None = None

    advisors = _catalog.get_personas_by_group("advisory")
    researcher = next((a for a in advisors if a.id == "researcher"), None)
    others = [a for a in advisors if a.id != "researcher"]
    selected_advisors = ([researcher] if researcher else []) + others[:1]

    tasks: List[Task] = []

    def build_motivator_task(persona):
        async def _run() -> PersonaEvaluation:
            advisor_notes: List[str] = []
            for advisor in selected_advisors:
                note = _llm.advise(advisor.id, job, resume_context)
                advisor_notes.append(note)
            result = _llm.evaluate(persona.id, persona.decision_lens, job, resume_context)
            reason = result["reason"]
            if advisor_notes:
                reason = reason + " | " + "; ".join(advisor_notes)
            evaluation = PersonaEvaluation(
                job_id=job_id,
                persona_id=persona.id,
                vote_bool=result["vote"],
                confidence=result["confidence"],
                reason_text=reason,
                provider=result["provider"],
                latency_ms=result["latency_ms"],
            )
            motivator_evals.append(evaluation)
            all_evals.append(evaluation)
            if _db.initialized:
                try:
                    await _db.insert_persona_evaluation(evaluation)
                except Exception as e:  # pragma: no cover - db optional
                    logger.error(f"Failed to persist evaluation: {e}")
            return evaluation
        return _run

    for persona in _catalog.get_personas_by_group("motivational"):
        tasks.append(Task(name=persona.id, coro=build_motivator_task(persona)))

    def build_decision_task(persona):
        async def _run() -> PersonaEvaluation:
            approvals = sum(1 for e in motivator_evals if e.vote_bool)
            total = len(motivator_evals) or 1
            majority = approvals / total
            vote = majority >= 0.5
            reason = f"{approvals}/{total} motivators approve"
            evaluation = PersonaEvaluation(
                job_id=job_id,
                persona_id=persona.id,
                vote_bool=vote,
                confidence=majority,
                reason_text=reason,
                provider="google",
                latency_ms=0,
            )
            decision_evals.append(evaluation)
            all_evals.append(evaluation)
            if _db.initialized:
                try:
                    await _db.insert_persona_evaluation(evaluation)
                except Exception as e:  # pragma: no cover - db optional
                    logger.error(f"Failed to persist decision eval: {e}")
            return evaluation
        return _run

    for persona in _catalog.get_personas_by_group("decision"):
        tasks.append(Task(name=persona.id, coro=build_decision_task(persona)))

    async def judge_task() -> Decision:
        nonlocal final_decision
        approvals = sum(1 for e in decision_evals if e.vote_bool)
        total = len(decision_evals) or 1
        final_vote = approvals / total >= 0.5
        confidence = approvals / total
        reason = f"{approvals}/{total} decision personas approve"
        decision = Decision(
            job_id=job_id,
            final_decision_bool=final_vote,
            confidence=confidence,
            reason_text=reason,
            created_at=datetime.now(timezone.utc),
        )
        final_decision = decision
        if _db.initialized:
            try:
                await _db.insert_decision(decision)
            except Exception as e:  # pragma: no cover - db optional
                logger.error(f"Failed to persist final decision: {e}")
        return decision

    tasks.append(Task(name="judge", coro=judge_task))

    crew = Crew(tasks)
    await crew.run()

    summary = EvaluationSummary(job_id=job_id, evaluations=all_evals, decision=final_decision)
    logger.info(f"Completed evaluation for job {job_id}")
    return summary
