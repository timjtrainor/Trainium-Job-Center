"""Job posting review package with refactored CrewAI architecture."""

from .orchestrator import (
    JobPostingOrchestrator,
    evaluate_job_posting,
    evaluate_job_posting_async,
    get_job_posting_orchestrator,
)
from .crew import JobPostingReviewCrew, get_job_posting_review_crew, run_crew
from .rules import (
    JobPostingInput,
    PersonaAnalysis,
    EvaluationSummary,
    generate_job_id,
    validate_job_posting,
    deduplicate_items,
    extract_json_from_crew_output,
)

__all__ = [
    # Main orchestration
    "JobPostingOrchestrator",
    "evaluate_job_posting",
    "evaluate_job_posting_async",
    "get_job_posting_orchestrator",

    # Crew definitions
    "JobPostingReviewCrew",
    "get_job_posting_review_crew",
    "run_crew",

    # Data models and utilities
    "JobPostingInput",
    "PersonaAnalysis",
    "EvaluationSummary",
    "generate_job_id",
    "validate_job_posting",
    "deduplicate_items",
    "extract_json_from_crew_output",
]
