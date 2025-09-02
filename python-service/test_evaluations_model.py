import pytest
from pydantic import ValidationError

from app.models.evaluations import PersonaEvaluation, Decision


def test_persona_evaluation_confidence_validation():
    """PersonaEvaluation rejects confidence outside [0, 1]."""
    with pytest.raises(ValidationError):
        PersonaEvaluation(
            job_id="job",
            persona_id="persona",
            vote_bool=True,
            confidence=1.5,
            reason_text="reason",
            provider="provider",
            latency_ms=10,
        )
    with pytest.raises(ValidationError):
        PersonaEvaluation(
            job_id="job",
            persona_id="persona",
            vote_bool=True,
            confidence=-0.1,
            reason_text="reason",
            provider="provider",
            latency_ms=10,
        )


def test_decision_confidence_validation():
    """Decision rejects confidence outside [0, 1]."""
    with pytest.raises(ValidationError):
        Decision(
            job_id="job",
            final_decision_bool=True,
            confidence=1.2,
            reason_text="reason",
        )
    with pytest.raises(ValidationError):
        Decision(
            job_id="job",
            final_decision_bool=True,
            confidence=-0.2,
            reason_text="reason",
        )
