"""Job Review CrewAI implementation with early termination support."""

from typing import Any, Dict
from loguru import logger
from pathlib import Path

from ...ai.evaluation_pipeline import EvaluationPipeline, _default_pipeline
from ...persona_loader import PersonaCatalog
from ...ai.persona_llm import PersonaLLM
try:
    from ...infrastructure.database import get_database_service
except Exception:  # pragma: no cover - fallback when asyncpg missing
    class DatabaseService:  # type: ignore
        initialized = False
    def get_database_service() -> DatabaseService:  # type: ignore
        return DatabaseService()


class JobReviewResult:
    """Wrapper for job review results that provides CrewAI-like interface."""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        
    @property
    def raw(self) -> Dict[str, Any]:
        """Return raw result data in expected format."""
        return self._data


class JobReviewTask:
    """Wrapper that provides CrewAI-like task interface."""
    
    def __init__(self, pipeline: EvaluationPipeline):
        self.pipeline = pipeline
    
    def kickoff(self, inputs: Dict[str, Any]) -> JobReviewResult:
        """Execute job review synchronously and format results."""
        job_data = inputs.get("job", {})
        
        # Generate a job ID if not provided
        job_id = job_data.get("id") or job_data.get("job_id") or f"review_{hash(str(job_data))}"
        
        # For now, run synchronously - will need async wrapper in real implementation
        import asyncio
        try:
            # Run the evaluation pipeline
            summary = asyncio.run(self.pipeline.evaluate_job(job_id, job_data, ""))
            
            # Format response to match expected structure
            formatted_result = self._format_evaluation_summary(summary, job_id)
            return JobReviewResult(formatted_result)
            
        except Exception as e:
            logger.error(f"Job review failed: {e}")
            # Return error response in expected format
            return JobReviewResult(self._format_error_response(job_id, str(e)))
    
    def _format_evaluation_summary(self, summary, job_id: str) -> Dict[str, Any]:
        """Format EvaluationSummary into expected API response format."""
        
        # Extract persona evaluations
        personas = []
        for eval in summary.evaluations:
            personas.append({
                "id": eval.persona_id,
                "recommend": eval.vote_bool,
                "reason": eval.reason_text
            })
        
        # Determine final recommendation
        final_recommend = summary.decision.final_decision_bool if summary.decision else False
        final_rationale = summary.decision.reason_text if summary.decision else "No decision available"
        final_confidence = "high" if summary.decision and summary.decision.confidence > 0.7 else "medium" if summary.decision and summary.decision.confidence > 0.4 else "low"
        
        # Extract any analysis data
        tradeoffs = []
        actions = []
        sources = [eval.persona_id for eval in summary.evaluations]
        
        # Look for brand alignment in analysis
        brand_alignment = summary.analysis.get("brand_alignment_score", 0)
        if brand_alignment < 5:  # Low score threshold
            actions.append("Consider salary negotiation")
            actions.append("Evaluate role fit carefully")
        
        return {
            "job_id": job_id,
            "correlation_id": None,
            "final": {
                "recommend": final_recommend,
                "rationale": final_rationale,
                "confidence": final_confidence
            },
            "personas": personas,
            "tradeoffs": tradeoffs,
            "actions": actions,
            "sources": sources
        }
    
    def _format_error_response(self, job_id: str, error_message: str) -> Dict[str, Any]:
        """Format error response in expected format."""
        return {
            "job_id": job_id,
            "correlation_id": None,
            "final": {
                "recommend": False,
                "rationale": f"Analysis failed: {error_message}",
                "confidence": "low"
            },
            "personas": [{
                "id": "error_handler", 
                "recommend": False,
                "reason": f"Crew execution failed: {error_message}"
            }],
            "tradeoffs": [],
            "actions": [
                "Review crew configuration",
                "Check system dependencies"
            ],
            "sources": ["error_handler"]
        }


class JobReviewCrew:
    """Job Review CrewAI implementation using evaluation pipeline."""
    
    def __init__(self, pipeline: EvaluationPipeline = None):
        self.pipeline = pipeline or _default_pipeline
        
    def job_review(self) -> JobReviewTask:
        """Return job review task."""
        return JobReviewTask(self.pipeline)


def get_job_review_crew() -> JobReviewCrew:
    """Get default job review crew instance."""
    return JobReviewCrew()