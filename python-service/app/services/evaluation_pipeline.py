"""Crew-based job evaluation pipeline orchestrating personas."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
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


async def evaluate_job(job_id: str, job: Dict[str, Any], user_id: str) -> EvaluationSummary:
    """Run motivational personas against a job with user resume context."""
    logger.info(f"Starting evaluation for job {job_id}")
    resume_context: Dict[str, Any] = {}
    if _db.initialized and user_id:
        try:
            resume_context = await _db.get_user_resume_context(user_id)
        except Exception as e:
            logger.error(f"Failed to load resume context: {e}")
    evaluations: List[PersonaEvaluation] = []
    for persona in _catalog.get_personas_by_group("motivational"):
        advisor_notes = []
        advisors = _catalog.get_personas_by_group("advisory")
        researcher = next((a for a in advisors if a.id == "researcher"), None)
        others = [a for a in advisors if a.id != "researcher"]
        selected = ([researcher] if researcher else []) + others[:1]
        for advisor in selected:
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
        evaluations.append(evaluation)
        if _db.initialized:
            try:
                await _db.insert_persona_evaluation(evaluation)
            except Exception as e:
                logger.error(f"Failed to persist evaluation: {e}")
    decision_evals = await evaluate_decision_personas(job_id, evaluations)
    final_decision = await aggregate_decision(job_id, decision_evals)
    summary = EvaluationSummary(job_id=job_id, evaluations=evaluations, decision=final_decision)
    logger.info(f"Completed evaluation for job {job_id}")
    return summary


async def evaluate_decision_personas(job_id: str, motivators: List[PersonaEvaluation]) -> List[PersonaEvaluation]:
    """Run decision personas based on motivational outputs."""
    approvals = sum(1 for e in motivators if e.vote_bool)
    total = len(motivators) or 1
    majority = approvals / total
    decision_evals: List[PersonaEvaluation] = []
    for persona in _catalog.get_personas_by_group("decision"):
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
        if _db.initialized:
            try:
                await _db.insert_persona_evaluation(evaluation)
            except Exception as e:
                logger.error(f"Failed to persist decision eval: {e}")
    return decision_evals


async def aggregate_decision(job_id: str, decisions: List[PersonaEvaluation]) -> Decision:
    """Judge persona synthesizes final decision."""
    approvals = sum(1 for e in decisions if e.vote_bool)
    total = len(decisions) or 1
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
    if _db.initialized:
        try:
            await _db.insert_decision(decision)
        except Exception as e:
            logger.error(f"Failed to persist final decision: {e}")
    return decision
