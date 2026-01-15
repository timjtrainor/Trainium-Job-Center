"""Utilities for routing persona requests to provider-specific LLMs."""
from __future__ import annotations

from typing import Dict, Any, Tuple

from .ai_service import ai_service


class PersonaLLM:
    """Dispatches persona calls to provider/model specific clients.

    The class uses the unified AIService for execution.
    """

    def __init__(self) -> None:
        pass

    def advise(
        self,
        advisor_id: str,
        job: Dict[str, Any],
        context: Dict[str, Any] | None = None,
        *,
        provider: str = None,
        model: str = None,
    ) -> str:
        """Generate advisory notes for a persona."""
        
        # Construct the "User Input" part of the prompt
        desc = job.get("description", "").lower()
        # Mirroring the logic from previous implementation to form the input
        base_prompt = (
            f"Please analyze this job description regarding salary info."
            if "salary" in desc
            else f"Please analyze this job description regarding lack of salary info."
        )
        if context and context.get("standard_job_roles"):
            base_prompt += f" Context: including {len(context['standard_job_roles'])} standard roles."
            
        # Execute via AI Service
        # We assume the prompt name in LangFuse follows convention "persona-{id}"
        prompt_name = f"persona-{advisor_id}"
        
        # Determine strict model override if passed (backwards compat)
        # Verify if 'provider/model' format is needed or just rely on LangFuse default
        # If legacy code passed provider="openai", model="gpt-4", we try to map or ignore
        # Ideally we let LangFuse control it, but if we must:
        # ai_service determines model from prompt config primarily.
        
        return ai_service.execute_prompt(
            prompt_name=prompt_name,
            variables={"user_input": base_prompt},
            label="production"
        )

    def evaluate(
        self,
        persona_id: str,
        decision_lens: str,
        job: Dict[str, Any],
        context: Dict[str, Any] | None = None,
        *,
        provider: str = None,
        model: str = None,
    ) -> Dict[str, Any]:
        """Evaluate a job from a persona's perspective."""
        
        desc = job.get("description", "").lower()
        
        user_input = f"Evaluate this job based on: {decision_lens}."
        if context and context.get("strategic_narratives"):
            user_input += " Consider strategic narratives provided."
            
        prompt_name = f"persona-{persona_id}"
        
        response_text = ai_service.execute_prompt(
            prompt_name=prompt_name,
            variables={"user_input": user_input},
            label="production"
        )
        
        vote = "approve" in response_text.lower() or "positive" in response_text.lower()
        
        return {
            "vote": vote,
            "reason": response_text,
            "confidence": 0.8,
            "provider": "ai_service",
            "model": "dynamic",
            "latency_ms": 0,
        }
