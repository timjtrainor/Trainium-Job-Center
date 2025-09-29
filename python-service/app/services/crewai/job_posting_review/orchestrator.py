"""Thin orchestrator for coordinating CrewAI job posting review workflow."""

from typing import Dict, Any, Optional
import asyncio
import hashlib
from datetime import datetime

# Career brand analysis - no specific schemas needed for internal processing
from .rules import (generate_job_id, validate_job_posting, get_current_iso_timestamp,
                   deduplicate_items, extract_json_from_crew_output)
from .crew import get_job_posting_review_crew
from ....services.feedback_transformer import get_feedback_transformer


class JobPostingOrchestrator:
    """Thin orchestrator that coordinates CrewAI execution without implementing business logic."""

    def __init__(self):
        self._crew_cache = None

    @property
    def crew(self):
        """Lazy-loaded cached crew instance."""
        if self._crew_cache is None:
            self._crew_cache = get_job_posting_review_crew()
        return self._crew_cache

    async def evaluate_job_posting_async(self, job_posting: Dict[str, Any],
                                       correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the CrewAI job posting review workflow asynchronously.

        This method coordinates the crew execution but delegates all business logic
        to the agents/tasks defined in the CrewAI configuration.
        """
        # Validate input data
        validated_job = validate_job_posting(job_posting)

        # Generate unique identifiers
        job_id = generate_job_id(job_posting)
        correlation_id = correlation_id or get_current_iso_timestamp()

        # Execute the CrewAI workflow
        try:
            # Run the crew with the job posting context
            result = self.crew.kickoff(inputs={
                "job_posting": validated_job.model_dump(),
                "job_id": job_id,
                "correlation_id": correlation_id
            })

            # Parse the crew result
            parsed_result = self._parse_crew_result(result, job_posting, correlation_id)

            # Apply feedback transformer for user-friendly explanations
            transformed_result = await self._apply_feedback_transformation(parsed_result)

            # Return structured dictionary with all necessary fields
            return transformed_result

        except Exception as e:
            # Return structured error response
            return {
                "job_id": job_id,
                "correlation_id": correlation_id,
                "error": f"CrewAI execution failed: {str(e)}",
                "job_intake": job_posting,
                "personas": [],
                "tradeoffs": [],
                "actions": [],
                "sources": [],
                "overall_alignment_score": 0
            }

    def evaluate_job_posting(self, job_posting: Dict[str, Any],
                           correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for job posting evaluation.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create new event loop in thread if current loop is running
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        self.evaluate_job_posting_async(job_posting, correlation_id)
                    )
                finally:
                    new_loop.close()
            else:
                return loop.run_until_complete(
                    self.evaluate_job_posting_async(job_posting, correlation_id)
                )
        except RuntimeError:
            # No event loop available
            return asyncio.run(self.evaluate_job_posting_async(job_posting, correlation_id))

    def _parse_crew_result(self, crew_result: Any, job_posting: Dict[str, Any],
                          correlation_id: str) -> Dict[str, Any]:
        """
        Parse and structure the CrewAI result.

        This method extracts data from the crew output but doesn't implement
        business logic - that remains in the agents/tasks.
        """
        # Handle different crew result formats
        if hasattr(crew_result, 'json_dict') and crew_result.json_dict:
            result_data = crew_result.json_dict
        elif hasattr(crew_result, 'raw') and crew_result.raw:
            result_data = extract_json_from_crew_output(crew_result.raw)
        elif isinstance(crew_result, (str, bytes)):
            result_data = extract_json_from_crew_output(str(crew_result))
        elif isinstance(crew_result, dict):
            result_data = crew_result
        else:
            result_data = {"raw_result": str(crew_result)}

        # Generate job ID if not present
        job_id = result_data.get('job_id') or generate_job_id(job_posting)

        # Structure the final output - let CrewAI logic determine content
        final_output = {
            "job_id": job_id,
            "correlation_id": correlation_id,
            "job_intake": job_posting,
            "pre_filter": result_data.get("pre_filter", {}),
            "quick_fit": None,  # Not used in current architecture
            "brand_match": result_data.get("brand_match"),
            "final": result_data.get("final", {
                "recommend": False,
                "rationale": "Analysis incomplete",
                "confidence": "low"
            }),
            "personas": result_data.get("personas", []),
            "tradeoffs": deduplicate_items(result_data.get("tradeoffs", [])),
            "actions": deduplicate_items(result_data.get("actions", [])),
            "sources": deduplicate_items(result_data.get("sources", []))
        }

        return final_output

    async def _apply_feedback_transformation(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply feedback transformer to convert technical outputs to user-friendly explanations
        and extract overall_alignment_score as top-level field for database and UI.
        """
        try:
            # Get the feedback transformer
            transformer = get_feedback_transformer()

            # Apply transformation to get readable explanations
            transformed = await transformer.transform_feedback(analysis_result)

            # Ensure overall_alignment_score is available at top level for database/UI
            if "brand_match" in transformed and transformed["brand_match"]:
                brand_match = transformed["brand_match"]
                if "overall_alignment_score" in brand_match:
                    # Copy to top level for easy database access and UI display
                    transformed["overall_alignment_score"] = brand_match["overall_alignment_score"]
                else:
                    # Fallback: calculate from individual scores if available
                    overall_score = self._calculate_fallback_alignment_score(brand_match)
                    transformed["overall_alignment_score"] = overall_score
                    if "brand_match" in transformed and isinstance(transformed["brand_match"], dict):
                        transformed["brand_match"]["overall_alignment_score"] = overall_score
            else:
                # Default for missing analysis
                transformed["overall_alignment_score"] = 0

            return transformed

        except Exception as e:
            # Log error but return original result to avoid breaking the flow
            print(f"Feedback transformation failed: {e}")
            # Ensure overall_alignment_score exists even if transformation fails
            if "overall_alignment_score" not in analysis_result:
                analysis_result["overall_alignment_score"] = 0
            return analysis_result

    def _calculate_fallback_alignment_score(self, brand_match: Dict[str, Any]) -> float:
        """
        Fallback calculation of overall alignment score from individual dimension scores.
        Uses the same weighting as the brand_match_manager for consistency.
        """
        try:
            dimensions = [
                "north_star", "trajectory_mastery", "values_compass", "lifestyle_alignment",
                "compensation_philosophy", "purpose_impact", "industry_focus", "company_filters", "constraints"
            ]

            scores = {}
            for dim in dimensions:
                if dim in brand_match and isinstance(brand_match[dim], dict) and "score" in brand_match[dim]:
                    # Convert 1-5 scores to 0-10 scale for overall calculation
                    score_1_5 = brand_match[dim]["score"]
                    score_0_10 = 2 + (score_1_5 - 1) * 2  # Convert 1->2, 5->10
                    scores[dim] = score_0_10

            if not scores:
                return 0

            # Apply user-specified weights
            weights = {
                "constraints": 0.25,
                "compensation_philosophy": 0.20,
                "trajectory_mastery": 0.18,
                "north_star": 0.15,
                "values_compass": 0.10,
                "lifestyle_alignment": 0.08,
                "purpose_impact": 0.03,
                "industry_focus": 0.01,
                "company_filters": 0.00
            }

            # Calculate weighted average
            total_weight = 0
            weighted_sum = 0

            for dim, weight in weights.items():
                if dim in scores:
                    weighted_sum += scores[dim] * weight
                    total_weight += weight

            return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0

        except Exception as e:
            print(f"Fallback alignment score calculation failed: {e}")
            return 0


# Global orchestrator instance for reuse
_orchestrator_instance: Optional[JobPostingOrchestrator] = None


def get_job_posting_orchestrator() -> JobPostingOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = JobPostingOrchestrator()
    return _orchestrator_instance


def evaluate_job_posting(job_posting: Dict[str, Any],
                        correlation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function for job posting evaluation using global orchestrator.
    """
    orchestrator = get_job_posting_orchestrator()
    return orchestrator.evaluate_job_posting(job_posting, correlation_id)


async def evaluate_job_posting_async(job_posting: Dict[str, Any],
                                   correlation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function for async job posting evaluation using global orchestrator.
    """
    orchestrator = get_job_posting_orchestrator()
    return await orchestrator.evaluate_job_posting_async(job_posting, correlation_id)
