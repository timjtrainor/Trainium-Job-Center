from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Optional


class PersonaEvaluation(BaseModel):
    """Record of a single persona's evaluation of a job."""
    job_id: str
    persona_id: str
    vote_bool: bool
    confidence: float
    reason_text: str
    provider: str
    latency_ms: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Decision(BaseModel):
    """Final decision produced by judge persona."""
    job_id: str
    final_decision_bool: bool
    confidence: float
    reason_text: str
    method: str = "judge"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvaluationSummary(BaseModel):
    """Summary of evaluations and final decision for a job."""
    job_id: str
    evaluations: List[PersonaEvaluation]
    decision: Optional[Decision] = None
