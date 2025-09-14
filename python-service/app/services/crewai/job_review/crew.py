"""Job Review CrewAI implementation with early termination support."""

from typing import Any, Dict
from loguru import logger


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
    
    def __init__(self, pipeline=None):
        self.pipeline = pipeline
    
    def kickoff(self, inputs: Dict[str, Any]) -> JobReviewResult:
        """Execute job review synchronously and format results."""
        job_data = inputs.get("job", {})
        
        # Generate a job ID if not provided
        job_id = job_data.get("id") or job_data.get("job_id") or f"review_{hash(str(job_data))}"
        
        try:
            if self.pipeline:
                # Use the actual evaluation pipeline
                import asyncio
                summary = asyncio.run(self.pipeline.evaluate_job(job_id, job_data, ""))
                formatted_result = self._format_evaluation_summary(summary, job_id)
            else:
                # Fallback for testing/development
                formatted_result = self._format_mock_response(job_id, job_data)
                
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
    
    def _format_mock_response(self, job_id: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format mock response for testing."""
        # Simple mock logic based on job data
        description = job_data.get("description", "").lower()
        salary = job_data.get("salary", "")
        
        # Mock persona evaluations
        personas = []
        
        # Brand fit persona - reject if salary looks low
        if "50" in salary or "low" in description:
            personas.append({
                "id": "brand_fit",
                "recommend": False,
                "reason": "Salary below brand expectations"
            })
        else:
            personas.append({
                "id": "brand_fit", 
                "recommend": True,
                "reason": "Good brand alignment"
            })
        
        # Culture match persona
        if "remote" in description:
            personas.append({
                "id": "culture_match",
                "recommend": True,
                "reason": "Remote work aligns with culture preferences"
            })
        else:
            personas.append({
                "id": "culture_match",
                "recommend": False,
                "reason": "No remote work options"
            })
        
        # Overall decision based on personas
        approval_count = sum(1 for p in personas if p["recommend"])
        final_recommend = approval_count > len(personas) / 2
        
        return {
            "job_id": job_id,
            "correlation_id": None,
            "final": {
                "recommend": final_recommend,
                "rationale": f"{'Approved' if final_recommend else 'Rejected'} based on {approval_count}/{len(personas)} persona approvals",
                "confidence": "medium"
            },
            "personas": personas,
            "tradeoffs": [],
            "actions": ["Review compensation if rejected", "Consider culture fit"],
            "sources": [p["id"] for p in personas]
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
    
    def __init__(self, pipeline=None):
        # Lazy import to avoid dependency issues
        if pipeline is None:
            try:
                from ...ai.evaluation_pipeline import _default_pipeline
                self.pipeline = _default_pipeline
            except ImportError:
                logger.warning("Could not import evaluation pipeline, using fallback mode")
                self.pipeline = None
        else:
            self.pipeline = pipeline
        
    def job_review(self) -> JobReviewTask:
        """Return job review task."""
        return JobReviewTask(self.pipeline)


def get_job_review_crew() -> JobReviewCrew:
    """Get default job review crew instance."""
    return JobReviewCrew()