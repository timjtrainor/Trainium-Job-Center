"""Utilities for routing persona requests to provider-specific LLMs."""
from __future__ import annotations

from typing import Dict, Any, Tuple

from .llm_clients import BaseLLMClient, create_llm_client


class PersonaLLM:
    """Dispatches persona calls to provider/model specific clients.

    The class lazily instantiates LLM clients and caches them so that
    multiple personas using the same ``(provider, model)`` pair share the
    underlying client instance.
    """

    def __init__(self) -> None:
        self._clients: Dict[Tuple[str, str], BaseLLMClient] = {}

    def _get_client(self, provider: str, model: str) -> BaseLLMClient:
        key = (provider, model)
        if key not in self._clients:
            self._clients[key] = create_llm_client(provider, model)
        return self._clients[key]

    def advise(
        self,
        advisor_id: str,
        job: Dict[str, Any],
        context: Dict[str, Any] | None = None,
        *,
        provider: str,
        model: str,
    ) -> str:
        """Generate advisory notes for a persona."""

        client = self._get_client(provider, model)
        desc = job.get("description", "").lower()
        base = (
            f"{advisor_id} notes salary info"
            if "salary" in desc
            else f"{advisor_id} finds no salary info"
        )
        if context and context.get("standard_job_roles"):
            base += f" with roles {len(context['standard_job_roles'])}"
        client.generate(base)  # placeholder call to demonstrate dispatch
        return base

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
        """Evaluate a job from a persona's perspective."""

        client = self._get_client(provider, model)
        desc = job.get("description", "").lower()
        approve = "remote" in desc or "flexible" in desc
        reason = f"{persona_id} {'approves' if approve else 'rejects'}: {decision_lens}"
        if context and context.get("strategic_narratives"):
            reason += " | narratives considered"
        client.generate(reason)  # placeholder dispatch
        return {
            "vote": approve,
            "reason": reason,
            "confidence": 0.8 if approve else 0.2,
            "provider": provider,
            "model": model,
            "latency_ms": 0,
        }
