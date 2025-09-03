"""Utilities for routing persona requests to provider-specific LLMs."""
from __future__ import annotations

from typing import Dict, Any, Tuple

from .llm_clients import BaseLLMClient, create_llm_client, LLMRouter
from ..core.config import get_settings


class PersonaLLM:
    """Dispatches persona calls to provider/model specific clients.

    The class uses the new LLM router for automatic provider selection and fallback.
    It maintains backwards compatibility with the existing interface while providing
    improved reliability through the routing mechanism.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._router = LLMRouter(preferences=settings.llm_preference)
        self._clients: Dict[Tuple[str, str], BaseLLMClient] = {}  # For backwards compatibility

    def _get_client(self, provider: str, model: str) -> BaseLLMClient:
        # This method is kept for backwards compatibility but is now deprecated
        # The router handles provider selection automatically
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
        provider: str = None,  # Now optional - uses router if not specified
        model: str = None,     # Now optional - uses router if not specified
    ) -> str:
        """Generate advisory notes for a persona."""
        
        # Use router if provider/model not specified (preferred approach)
        if provider is None or model is None:
            desc = job.get("description", "").lower()
            base_prompt = (
                f"{advisor_id} notes salary info"
                if "salary" in desc
                else f"{advisor_id} finds no salary info"
            )
            if context and context.get("standard_job_roles"):
                base_prompt += f" with roles {len(context['standard_job_roles'])}"
            
            return self._router.generate(base_prompt)
        else:
            # Backwards compatibility - use specific provider/model
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
        provider: str = None,  # Now optional - uses router if not specified
        model: str = None,     # Now optional - uses router if not specified
    ) -> Dict[str, Any]:
        """Evaluate a job from a persona's perspective."""
        
        desc = job.get("description", "").lower()
        approve = "remote" in desc or "flexible" in desc
        
        # Use router if provider/model not specified (preferred approach)
        if provider is None or model is None:
            reason_prompt = f"{persona_id} {'approves' if approve else 'rejects'}: {decision_lens}"
            if context and context.get("strategic_narratives"):
                reason_prompt += " | narratives considered"
            
            reason = self._router.generate(reason_prompt)
            return {
                "vote": approve,
                "reason": reason,
                "confidence": 0.8 if approve else 0.2,
                "provider": "router",  # Indicates router was used
                "model": "auto",       # Model selected by router
                "latency_ms": 0,
            }
        else:
            # Backwards compatibility - use specific provider/model
            client = self._get_client(provider, model)
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
