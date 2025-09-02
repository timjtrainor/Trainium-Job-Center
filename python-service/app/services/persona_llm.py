"""Deterministic LLM used for persona evaluations in tests."""
from typing import Dict, Any


class PersonaLLM:
    """Simple heuristic LLM replacement for tests."""

    def advise(self, advisor_id: str, job: Dict[str, Any], context: Dict[str, Any] | None = None) -> str:
        desc = job.get("description", "").lower()
        base = f"{advisor_id} notes salary info" if "salary" in desc else f"{advisor_id} finds no salary info"
        if context and context.get("standard_job_roles"):
            base += f" with roles {len(context['standard_job_roles'])}"
        return base

    def evaluate(
        self,
        persona_id: str,
        decision_lens: str,
        job: Dict[str, Any],
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        desc = job.get("description", "").lower()
        approve = "remote" in desc or "flexible" in desc
        reason = f"{persona_id} {'approves' if approve else 'rejects'}: {decision_lens}"
        if context and context.get("strategic_narratives"):
            reason += " | narratives considered"
        return {
            "vote": approve,
            "reason": reason,
            "confidence": 0.8 if approve else 0.2,
            "provider": "google",
            "model": "gemini-2.5-flash-lite",
            "latency_ms": 0,
        }
