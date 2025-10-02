"""Thin orchestrator for coordinating CrewAI job posting review workflow."""

from typing import Dict, Any, Optional
import json
import asyncio
import hashlib
from datetime import datetime
from loguru import logger

# Career brand analysis - import pydantic models for proper parsing
from .rules import (generate_job_id, validate_job_posting, get_current_iso_timestamp,
                   deduplicate_items, extract_json_from_crew_output)
from .crew import get_job_posting_review_crew
from ....services.feedback_transformer import get_feedback_transformer
from models.creaii_schemas import PreFilterResult, BrandMatchComplete


_TASK_KEY_ALIASES = {
    "pre_filter": "pre_filter_task",
    "north_star": "north_star_task",
    "trajectory_mastery": "trajectory_mastery_task",
    "values_compass": "values_compass_task",
    "lifestyle_alignment": "lifestyle_alignment_task",
    "compensation_philosophy": "compensation_philosophy_task",
    "purpose_impact": "purpose_impact_task",
    "industry_focus": "industry_focus_task",
    "company_filters": "company_filters_task",
    "constraints": "constraints_task",
    "brand_match": "brand_match_task",
}


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
        Execute the CrewAI job posting review workflow asynchronously with pre-filter optimization.

        This method coordinates the crew execution but delegates all business logic
        to the agents/tasks defined in the CrewAI configuration.

        OPTIMIZATION: Runs pre-filter first. If rejected, skips expensive analysis tasks.
        """
        # Validate input data
        validated_job = validate_job_posting(job_posting)

        # Generate unique identifiers
        job_id = generate_job_id(job_posting)
        correlation_id = correlation_id or get_current_iso_timestamp()

        # Execute the CrewAI workflow with pre-filter optimization
        try:
            # PHASE 1: Run pre-filter task only
            logger.info(f"🔍 Running pre-filter for job_id: {job_id}")
            pre_filter_result = await self._run_pre_filter(validated_job, job_id, correlation_id)

            # Check if pre-filter rejected the job
            if not pre_filter_result.get("recommend", True):
                logger.info(f"⏭️ Pre-filter rejected job_id: {job_id} - skipping analysis")
                logger.info(f"   Rejection reason: {pre_filter_result.get('reason', 'No reason provided')}")
                return self._build_pre_filter_rejection_response(
                    job_id, correlation_id, job_posting, pre_filter_result
                )

            logger.info(f"✅ Pre-filter passed for job_id: {job_id} - proceeding with full analysis")

            # PHASE 2: Run full crew with the job posting context
            result = self.crew.kickoff(inputs={
                "job_posting": validated_job.model_dump(),
                "job_id": job_id,
                "correlation_id": correlation_id
            })

            # DEBUG: Log what CrewAI actually returns
            print("🔍 DEBUG: CrewAI Raw Result:")
            if hasattr(result, 'raw') and result.raw:
                print(f"Raw output ({type(result.raw)}): {result.raw[:500]}...")
            if hasattr(result, 'json_dict') and result.json_dict:
                print("JSON dict:", json.dumps(result.json_dict, indent=2))
            if hasattr(result, 'tasks_output'):
                tasks_output = result.tasks_output
                if isinstance(tasks_output, dict):
                    keys = list(tasks_output.keys()) if tasks_output else []
                    print("Tasks output keys:", keys or "None")
                    iterable = tasks_output.items()
                elif isinstance(tasks_output, list):
                    print("Tasks output list length:", len(tasks_output))
                    iterable = []
                    for idx, entry in enumerate(tasks_output):
                        if isinstance(entry, dict):
                            name = entry.get("task_name") or entry.get("name") or f"task_{idx}"
                            payload = entry.get("output") or entry.get("result") or entry
                        else:
                            name = f"task_{idx}"
                            payload = entry
                        iterable.append((name, payload))
                else:
                    print("Tasks output type:", type(tasks_output))
                    iterable = []

                for task_name, task_output in iterable:
                    if task_output:
                        print(f"  {task_name} -> {type(task_output)}: {str(task_output)[:100]}...")
            print("=== END CREW OUTPUT ===")

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

    async def _run_pre_filter(self, validated_job: Any, job_id: str, correlation_id: str) -> Dict[str, Any]:
        """Run only the pre-filter task to check if job should be analyzed."""
        from .crew import JobPostingReviewCrew

        # Create a minimal crew with just pre-filter agent and task
        crew_config = JobPostingReviewCrew()
        pre_filter_agent = crew_config.pre_filter_agent()
        pre_filter_task = crew_config.pre_filter_task()

        # Execute just the pre-filter task
        from crewai import Crew, Process
        mini_crew = Crew(
            agents=[pre_filter_agent],
            tasks=[pre_filter_task],
            process=Process.sequential,
            verbose=False,
        )

        result = mini_crew.kickoff(inputs={
            "job_posting": validated_job.model_dump(),
            "job_id": job_id,
            "correlation_id": correlation_id
        })

        # Extract the pre-filter result from TaskOutput
        if hasattr(result, 'tasks_output') and result.tasks_output:
            tasks_output = result.tasks_output
            if isinstance(tasks_output, list) and len(tasks_output) > 0:
                task_output = tasks_output[0]
            elif isinstance(tasks_output, dict):
                task_output = tasks_output.get('pre_filter_task')
            else:
                task_output = None

            if task_output:
                if hasattr(task_output, 'pydantic') and task_output.pydantic:
                    if hasattr(task_output.pydantic, 'model_dump'):
                        return task_output.pydantic.model_dump()
                    elif hasattr(task_output.pydantic, 'dict'):
                        return task_output.pydantic.dict()
                elif hasattr(task_output, 'json_dict') and task_output.json_dict:
                    return task_output.json_dict

        # Default to recommend if extraction failed
        logger.warning("Failed to extract pre-filter result, defaulting to recommend=True")
        return {"recommend": True, "reason": None}

    def _build_pre_filter_rejection_response(self, job_id: str, correlation_id: str,
                                            job_posting: Dict[str, Any],
                                            pre_filter_result: Dict[str, Any]) -> Dict[str, Any]:
        """Build response for jobs rejected by pre-filter without running full analysis."""
        return {
            "job_id": job_id,
            "correlation_id": correlation_id,
            "job_intake": job_posting,
            "pre_filter": {
                "recommend": False,
                "reason": pre_filter_result.get("reason", "Pre-filter rejection")
            },
            "final": {
                "recommend": False,
                "confidence": "high",
                "rationale": f"Pre-filter rejection: {pre_filter_result.get('reason', 'Job does not meet basic criteria')}",
                "constraint_issues": "none"
            },
            "personas": [],
            "tradeoffs": [],
            "actions": [],
            "sources": [],
            "overall_alignment_score": 0
        }

    def _error_response(self, job_id: str, correlation_id: str,
                       job_posting: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "job_id": job_id,
            "correlation_id": correlation_id,
            "error": error_msg,
            "job_intake": job_posting,
            "personas": [],
            "tradeoffs": [],
            "actions": [],
            "sources": [],
            "overall_alignment_score": 0
        }

    def _parse_crew_result(self, crew_result: Any, job_posting: Dict[str, Any],
                          correlation_id: str) -> Dict[str, Any]:
        """
        Extract validated BrandMatchComplete result from CrewAI and convert to worker-expected format.
        """
        job_id = generate_job_id(job_posting)

        # Validate crew_result structure
        if not hasattr(crew_result, 'tasks_output'):
            logger.error("CrewAI result missing tasks_output attribute")
            return self._error_response(job_id, correlation_id, job_posting,
                                       "Invalid CrewAI result structure: missing tasks_output")

        if not crew_result.tasks_output:
            logger.error("CrewAI tasks_output is empty")
            return self._error_response(job_id, correlation_id, job_posting,
                                       "CrewAI returned empty tasks_output")

        # Extract the brand match manager result (should be a validated BrandMatchComplete Pydantic object)
        brand_match_result = None
        tasks_output = crew_result.tasks_output

        # Handle both list and dict formats
        if isinstance(tasks_output, list):
            if len(tasks_output) < 10:
                logger.warning(f"Expected 10 tasks, got {len(tasks_output)}")

            # tasks_output is a list - find the last item (brand_match_task is the final task)
            brand_match_result = tasks_output[-1] if tasks_output else None
        elif isinstance(tasks_output, dict):
            brand_match_result = tasks_output.get('brand_match_task')
        else:
            logger.error(f"Unexpected tasks_output type: {type(tasks_output)}")
            return self._error_response(job_id, correlation_id, job_posting,
                                       f"Invalid tasks_output type: {type(tasks_output)}")

        if brand_match_result is None:
            logger.warning("No brand_match_task result found in crew output")
            return self._error_response(job_id, correlation_id, job_posting,
                                       "CrewAI did not produce a brand match result")

        # Extract data from TaskOutput object
        # TaskOutput has attributes: pydantic, json_dict, raw, etc.
        brand_data = None

        if hasattr(brand_match_result, 'pydantic') and brand_match_result.pydantic:
            # TaskOutput.pydantic contains the validated Pydantic model
            logger.info("Extracting brand_data from TaskOutput.pydantic")
            if hasattr(brand_match_result.pydantic, 'model_dump'):
                brand_data = brand_match_result.pydantic.model_dump()
            elif hasattr(brand_match_result.pydantic, 'dict'):
                brand_data = brand_match_result.pydantic.dict()
        elif hasattr(brand_match_result, 'json_dict') and brand_match_result.json_dict:
            # Fallback to json_dict if pydantic not available
            logger.info("Extracting brand_data from TaskOutput.json_dict")
            brand_data = brand_match_result.json_dict
        elif hasattr(brand_match_result, 'model_dump'):
            # Direct Pydantic model (shouldn't happen but handle it)
            logger.info("Extracting brand_data from direct Pydantic model")
            brand_data = brand_match_result.model_dump()
        elif isinstance(brand_match_result, dict):
            # Already a dict
            logger.info("brand_match_result is already a dict")
            brand_data = brand_match_result
        else:
            logger.error(f"Cannot extract data from brand_match_result type: {type(brand_match_result)}")
            logger.error(f"Available attributes: {dir(brand_match_result)}")
            return self._error_response(job_id, correlation_id, job_posting,
                                       f"Cannot extract data from TaskOutput: {type(brand_match_result)}")

        # Validate brand_data was extracted successfully
        if brand_data is None:
            logger.error("brand_data extraction resulted in None")
            return self._error_response(job_id, correlation_id, job_posting,
                                       "Failed to extract brand_data from TaskOutput")

        logger.info(f"Successfully extracted brand_data with keys: {list(brand_data.keys())}")

        # Extract pre-filter result
        pre_filter_result = None
        if isinstance(tasks_output, list):
            # pre_filter_task is the first task (index 0)
            pre_filter_result = tasks_output[0] if len(tasks_output) > 0 else None
        elif isinstance(tasks_output, dict):
            pre_filter_result = tasks_output.get('pre_filter_task')

        # Convert to worker-expected format
        final = {
            "recommend": brand_data.get("recommend", False),
            "confidence": brand_data.get("confidence", "low"),
            "rationale": brand_data.get("overall_summary", "No analysis available"),
            "constraint_issues": brand_data.get("constraint_issues", "none")
        }

        pre_filter = {}
        if pre_filter_result:
            # Extract from TaskOutput same way as brand_match_result
            pre_filter_data = None
            if hasattr(pre_filter_result, 'pydantic') and pre_filter_result.pydantic:
                logger.info("Extracting pre_filter_data from TaskOutput.pydantic")
                if hasattr(pre_filter_result.pydantic, 'model_dump'):
                    pre_filter_data = pre_filter_result.pydantic.model_dump()
                elif hasattr(pre_filter_result.pydantic, 'dict'):
                    pre_filter_data = pre_filter_result.pydantic.dict()
            elif hasattr(pre_filter_result, 'json_dict') and pre_filter_result.json_dict:
                logger.info("Extracting pre_filter_data from TaskOutput.json_dict")
                pre_filter_data = pre_filter_result.json_dict
            elif hasattr(pre_filter_result, 'model_dump'):
                logger.info("Extracting pre_filter_data from direct Pydantic model")
                pre_filter_data = pre_filter_result.model_dump()
            elif isinstance(pre_filter_result, dict):
                logger.info("pre_filter_result is already a dict")
                pre_filter_data = pre_filter_result
            else:
                logger.warning(f"Cannot extract pre_filter_data from type: {type(pre_filter_result)}")
                pre_filter_data = {}

            if pre_filter_data:
                pre_filter = {
                    "recommend": pre_filter_data.get("recommend", True),
                    "reason": pre_filter_data.get("reason")
                }

        # Return structured data that matches worker expectations
        return {
            "job_id": job_id,
            "correlation_id": correlation_id,
            "job_intake": job_posting,
            "final": final,
            "pre_filter": pre_filter,
            "personas": [],  # Not implemented yet
            "tradeoffs": [],  # Not implemented yet
            "actions": [],  # Not implemented yet
            "sources": [],  # Not implemented yet
            "overall_alignment_score": brand_data.get("overall_alignment_score", 0)
        }

    def _normalize_task_outputs(self, result_data: Any) -> Dict[str, Any]:
        if not isinstance(result_data, dict):
            return {}

        normalized: Dict[str, Any] = {}
        for key, value in result_data.items():
            normalized[key] = self._coerce_output_value(value)

        for section_name in ("tasks_output", "tasks_outputs", "tasks_results", "results", "outputs"):
            section = result_data.get(section_name)
            if not section:
                continue
            flattened = self._flatten_task_section(section)
            for task_key, task_value in flattened.items():
                normalized.setdefault(task_key, task_value)

        for alias, task_key in _TASK_KEY_ALIASES.items():
            if alias not in normalized and task_key in normalized:
                normalized[alias] = normalized[task_key]

        return normalized

    def _flatten_task_section(self, section: Any) -> Dict[str, Any]:
        flattened: Dict[str, Any] = {}
        if isinstance(section, dict):
            for key, value in section.items():
                payload = self._extract_payload(value)
                flattened[key] = self._coerce_output_value(payload)
        elif isinstance(section, list):
            for entry in section:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("task_name") or entry.get("name") or entry.get("task") or entry.get("id") or entry.get("key")
                if not name:
                    continue
                payload = self._extract_payload(entry)
                flattened[name] = self._coerce_output_value(payload)
        return flattened

    def _extract_payload(self, candidate: Any) -> Any:
        current = candidate
        depth = 0
        while isinstance(current, dict) and depth < 6:
            for key in ("output", "final_output", "result", "response", "value", "data", "json_dict"):
                if key in current and current[key] is not None:
                    current = current[key]
                    break
            else:
                break
            depth += 1
        return current

    def _coerce_output_value(self, value: Any) -> Any:
        if value is None:
            return None

        if hasattr(value, "model_dump") and callable(value.model_dump):  # Pydantic v2
            try:
                return value.model_dump()
            except Exception:
                pass

        if hasattr(value, "dict") and callable(value.dict):  # Pydantic v1 compatibility
            try:
                return value.dict()
            except Exception:
                pass

        if isinstance(value, list):
            return [self._coerce_output_value(item) for item in value]

        if isinstance(value, tuple):
            return [self._coerce_output_value(item) for item in value]

        if isinstance(value, dict):
            payload = self._extract_payload(value)
            if payload is not value:
                return self._coerce_output_value(payload)
            return {k: self._coerce_output_value(v) for k, v in value.items()}

        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("{") or stripped.startswith("[") or stripped.startswith("```"):
                parsed = extract_json_from_crew_output(stripped)
                if isinstance(parsed, dict) and not parsed.get("parsing_error"):
                    return parsed
                if isinstance(parsed, list):
                    return parsed
            return value

        return value

    def _resolve_task_output(self, data: Dict[str, Any], *keys: str) -> Optional[Any]:
        for key in keys:
            value = data.get(key)
            if value is None:
                continue
            if isinstance(value, dict) and not value:
                continue
            return value
        return None

    def _resolve_list_output(self, value: Any) -> Any:
        if value is None:
            return []
        coerced = self._coerce_output_value(value)
        return coerced if isinstance(coerced, list) else []

    def _build_final_block(
        self,
        final_candidate: Optional[Dict[str, Any]],
        brand_match: Optional[Dict[str, Any]],
        pre_filter: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        final_block: Dict[str, Any] = {}

        if isinstance(final_candidate, dict):
            final_block.update(final_candidate)

        if isinstance(brand_match, dict):
            if final_block.get("recommend") is None and brand_match.get("recommend") is not None:
                final_block["recommend"] = brand_match.get("recommend")
            if final_block.get("confidence") is None and brand_match.get("confidence") is not None:
                final_block["confidence"] = brand_match.get("confidence")
            summary = brand_match.get("overall_summary") or brand_match.get("summary")
            if summary and not final_block.get("rationale"):
                final_block["rationale"] = summary
            if brand_match.get("constraint_issues") and not final_block.get("constraint_issues"):
                final_block["constraint_issues"] = brand_match.get("constraint_issues")

        if pre_filter.get("recommend") is False:
            final_block.setdefault("recommend", False)
            final_block.setdefault("confidence", "high")
            reason = pre_filter.get("reason")
            if reason:
                final_block.setdefault("rationale", f"Pre-filter rejection: {reason}")

        if not final_block:
            return None

        final_block.setdefault("recommend", False)
        final_block.setdefault("confidence", "low")
        final_block.setdefault("rationale", "Analysis summary unavailable.")
        final_block.setdefault("constraint_issues", "none")

        return final_block

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
