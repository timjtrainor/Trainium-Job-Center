"""Crew-based job evaluation pipeline orchestrating personas."""
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List
import time
from loguru import logger

from ..models.evaluations import PersonaEvaluation, Decision, EvaluationSummary
from .persona_loader import PersonaCatalog
from .persona_llm import PersonaLLM
try:
    from .database import DatabaseService, get_database_service
except Exception:  # pragma: no cover - fallback when asyncpg missing
    class DatabaseService:  # type: ignore
        initialized = False
        async def insert_persona_evaluation(self, *_, **__):
            return False
        async def insert_decision(self, *_, **__):
            return False

    def get_database_service() -> DatabaseService:  # type: ignore
        return DatabaseService()


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


class EvaluationPipeline:
    """Pipeline orchestrating persona evaluations."""

    def __init__(self, catalog: PersonaCatalog, llm: PersonaLLM, db: DatabaseService):
        self.catalog = catalog
        self.llm = llm
        self.db = db

    async def evaluate_decision_personas(
        self,
        job_id: str,
        job: Dict[str, Any],
        motivator_evals: List[PersonaEvaluation],
        all_evals: List[PersonaEvaluation],
    ) -> List[PersonaEvaluation]:
        """Run decision personas using LLM, informed by motivational outcomes."""
        decision_evals: List[PersonaEvaluation] = []
        context = {
            "motivator_outcomes": [
                {
                    "persona_id": e.persona_id,
                    "vote": e.vote_bool,
                    "confidence": e.confidence,
                    "reason": e.reason_text,
                }
                for e in motivator_evals
            ]
        }
        for persona in self.catalog.get_personas_by_group("decision"):
            start = time.monotonic()
            logger.info(f"Starting evaluation for persona {persona.id}")
            model = self.catalog.get_default_model(persona.id)
            result = self.llm.evaluate(
                persona.id,
                persona.decision_lens,
                job,
                context,
                provider=model["provider"],
                model=model["model"],
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                f"Completed evaluation for persona {persona.id} in {latency_ms} ms",
            )
            evaluation = PersonaEvaluation(
                job_id=job_id,
                persona_id=persona.id,
                vote_bool=result["vote"],
                confidence=result["confidence"],
                reason_text=result["reason"],
                provider=result["provider"],
                model=result["model"],
                latency_ms=latency_ms,
            )
            decision_evals.append(evaluation)
            all_evals.append(evaluation)
            if self.db.initialized:
                try:
                    await self.db.insert_persona_evaluation(evaluation)
                except Exception as e:  # pragma: no cover - db optional
                    logger.error(f"Failed to persist decision eval: {e}")
        return decision_evals

    async def aggregate_decision(
        self, job_id: str, job: Dict[str, Any], decision_evals: List[PersonaEvaluation]
    ) -> Decision:
        """Have the judge persona synthesize decision persona outcomes."""
        judge = self.catalog.get_personas_by_group("judge")[0]
        context = {
            "decision_outcomes": [
                {
                    "persona_id": e.persona_id,
                    "vote": e.vote_bool,
                    "confidence": e.confidence,
                    "reason": e.reason_text,
                }
                for e in decision_evals
            ]
        }
        start = time.monotonic()
        logger.info(f"Starting evaluation for persona {judge.id}")
        model = self.catalog.get_default_model(judge.id)
        result = self.llm.evaluate(
            judge.id,
            judge.decision_lens,
            job,
            context,
            provider=model["provider"],
            model=model["model"],
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            f"Completed evaluation for persona {judge.id} in {latency_ms} ms",
        )
        decision = Decision(
            job_id=job_id,
            final_decision_bool=result["vote"],
            confidence=result["confidence"],
            reason_text=result["reason"],
            created_at=datetime.now(timezone.utc),
        )
        if self.db.initialized:
            try:
                await self.db.insert_decision(decision)
            except Exception as e:  # pragma: no cover - db optional
                logger.error(f"Failed to persist final decision: {e}")
        return decision

    async def evaluate_job(
        self, job_id: str, job: Dict[str, Any], user_id: str
    ) -> EvaluationSummary:
        """Evaluate a job using a crew of motivational, decision, and judge personas."""
        logger.info(f"Starting evaluation for job {job_id}")
        resume_context: Dict[str, Any] = {}
        if self.db.initialized and user_id:
            try:
                resume_context = await self.db.get_user_resume_context(user_id)
            except Exception as e:
                logger.error(f"Failed to load resume context: {e}")

        all_evals: List[PersonaEvaluation] = []
        motivator_evals: List[PersonaEvaluation] = []

        advisors = self.catalog.get_personas_by_group("advisory")
        researcher = next((a for a in advisors if a.id == "researcher"), None)
        others = [a for a in advisors if a.id != "researcher"]
        selected_advisors = ([researcher] if researcher else []) + others[:1]

        tasks: List[Task] = []

        def build_motivator_task(persona):
            async def _run() -> PersonaEvaluation:
                advisor_notes: List[str] = []
                for advisor in selected_advisors:
                    model = self.catalog.get_default_model(advisor.id)
                    note = self.llm.advise(
                        advisor.id,
                        job,
                        resume_context,
                        provider=model["provider"],
                        model=model["model"],
                    )
                    advisor_notes.append(note)
                start = time.monotonic()
                logger.info(f"Starting evaluation for persona {persona.id}")
                model = self.catalog.get_default_model(persona.id)
                result = self.llm.evaluate(
                    persona.id,
                    persona.decision_lens,
                    job,
                    resume_context,
                    provider=model["provider"],
                    model=model["model"],
                )
                latency_ms = int((time.monotonic() - start) * 1000)
                logger.info(
                    f"Completed evaluation for persona {persona.id} in {latency_ms} ms",
                )
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
                    model=result["model"],
                    latency_ms=latency_ms,
                )
                motivator_evals.append(evaluation)
                all_evals.append(evaluation)
                if self.db.initialized:
                    try:
                        await self.db.insert_persona_evaluation(evaluation)
                    except Exception as e:  # pragma: no cover - db optional
                        logger.error(f"Failed to persist evaluation: {e}")
                return evaluation
            return _run

        for persona in self.catalog.get_personas_by_group("motivational"):
            tasks.append(Task(name=persona.id, coro=build_motivator_task(persona)))

        crew = Crew(tasks)
        await crew.run()

        decision_evals = await self.evaluate_decision_personas(
            job_id, job, motivator_evals, all_evals
        )
        final_decision = await self.aggregate_decision(job_id, job, decision_evals)

        summary = EvaluationSummary(
            job_id=job_id, evaluations=all_evals, decision=final_decision
        )
        logger.info(f"Completed evaluation for job {job_id}")
        return summary


# Default pipeline instance for convenience
_default_pipeline = EvaluationPipeline(
    PersonaCatalog(Path(__file__).with_name("persona_catalog.yaml")),
    PersonaLLM(),
    get_database_service(),
)
