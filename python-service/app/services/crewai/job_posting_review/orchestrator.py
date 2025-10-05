"""Thin orchestrator for coordinating CrewAI job posting review workflow."""

import os
import json
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

# Career brand analysis - import pydantic models for proper parsing
from .rules import (generate_job_id, validate_job_posting, get_current_iso_timestamp,
                   deduplicate_items, extract_json_from_crew_output)
from decimal import Decimal
from datetime import timezone

from .crew import get_job_posting_review_crew
from ....services.feedback_transformer import get_feedback_transformer
from .single_agent import BrandMatchSingleAgentEvaluator
from models.creaii_schemas import BrandMatchComplete


_TASK_KEY_ALIASES = {
    "pre_filter": "pre_filter_task",
    "north_star": "north_star_task",
    "trajectory_mastery": "trajectory_mastery_task",
    "values_compass": "values_compass_task",
    "lifestyle_alignment": "lifestyle_alignment_task",
    "compensation_philosophy": "compensation_philosophy_task",
    "brand_match": "brand_match_task",
}

_DIMENSION_KEYS = [
    "north_star",
    "trajectory_mastery",
    "values_compass",
    "lifestyle_alignment",
    "compensation_philosophy",
]


class JobPostingOrchestrator:
    """Thin orchestrator that coordinates CrewAI execution without implementing business logic."""

    def __init__(self):
        self._crew_cache = None
        self._single_agent_evaluator: Optional[BrandMatchSingleAgentEvaluator] = None
        flag_value = os.getenv("JOB_REVIEW_SINGLE_AGENT", "true").strip().lower()
        self._use_single_agent = flag_value not in {"0", "false", "no"}

    @property
    def crew(self):
        """Lazy-loaded cached crew instance."""
        if self._crew_cache is None:
            self._crew_cache = get_job_posting_review_crew()
        return self._crew_cache

    @property
    def single_agent_evaluator(self) -> BrandMatchSingleAgentEvaluator:
        if self._single_agent_evaluator is None:
            self._single_agent_evaluator = BrandMatchSingleAgentEvaluator()
        return self._single_agent_evaluator

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
            # PHASE 1: Run structured pre-filter using database fields
            logger.info(f"🔍 Running structured pre-filter for job_id: {job_id}")
            pre_filter_result = self._apply_structured_pre_filter(validated_job, job_posting)

            # Check if pre-filter rejected the job
            if not pre_filter_result.get("recommend", True):
                logger.info(f"⏭️ Pre-filter rejected job_id: {job_id} - skipping analysis")
                logger.info(f"   Rejection reason: {pre_filter_result.get('reason', 'No reason provided')}")
                return self._build_pre_filter_rejection_response(
                    job_id, correlation_id, job_posting, pre_filter_result
                )

            logger.info(f"✅ Pre-filter passed for job_id: {job_id} - proceeding with full analysis")

            if self._use_single_agent:
                try:
                    logger.info("⚙️ Running single-call evaluator with cached branding payload")
                    single_agent_result = await self._run_single_agent(
                        validated_job, job_posting, job_id, correlation_id, pre_filter_result
                    )
                    return single_agent_result
                except Exception as exc:
                    logger.error(f"Single-agent evaluation failed, falling back to CrewAI: {exc}")

            # PHASE 2: Run full crew with the job posting context
            result = self.crew.kickoff(inputs={
                "job_posting": validated_job.model_dump(),
                "job_id": job_id,
                "correlation_id": correlation_id
            })

            # DEBUG: Log what CrewAI actually returns (commented out for production)
            # print("🔍 DEBUG: CrewAI Raw Result:")
            # if hasattr(result, 'raw') and result.raw:
            #     print(f"Raw output ({type(result.raw)}): {result.raw[:500]}...")
            # if hasattr(result, 'json_dict') and result.json_dict:
            #     print("JSON dict:", json.dumps(result.json_dict, indent=2))
            # if hasattr(result, 'tasks_output'):
            #     tasks_output = result.tasks_output
            #     if isinstance(tasks_output, dict):
            #         keys = list(tasks_output.keys()) if tasks_output else []
            #         print("Tasks output keys:", keys or "None")
            #         iterable = tasks_output.items()
            #     elif isinstance(tasks_output, list):
            #         print("Tasks output list length:", len(tasks_output))
            #         iterable = []
            #         for idx, entry in enumerate(tasks_output):
            #             if isinstance(entry, dict):
            #                 name = entry.get("task_name") or entry.get("name") or f"task_{idx}"
            #                 payload = entry.get("output") or entry.get("result") or entry
            #             else:
            #                 name = f"task_{idx}"
            #                 payload = entry
            #             iterable.append((name, payload))
            #     else:
            #         print("Tasks output type:", type(tasks_output))
            #         iterable = []
            #
            #     for task_name, task_output in iterable:
            #         if task_output:
            #             print(f"  {task_name} -> {type(task_output)}: {str(task_output)[:100]}...")
            # print("=== END CREW OUTPUT ===")

            # Parse the crew result
            parsed_result = self._parse_crew_result(
                result,
                job_posting,
                correlation_id,
                pre_filter_override=pre_filter_result,
            )

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

    async def _run_single_agent(
        self,
        validated_job: Any,
        job_posting: Dict[str, Any],
        job_id: str,
        correlation_id: str,
        pre_filter_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute the single-call evaluator and build the worker response."""

        evaluator = self.single_agent_evaluator
        if not evaluator.is_available():
            raise RuntimeError("Single agent evaluator is not configured")

        evaluation = await evaluator.evaluate(validated_job.model_dump())
        brand_match_dict = evaluation.brand_match.model_dump()

        pre_filter = {
            "recommend": pre_filter_result.get("recommend", True),
            "reason": pre_filter_result.get("reason"),
        }

        final_block = {
            "recommend": brand_match_dict.get("recommend", False),
            "confidence": brand_match_dict.get("confidence", "low"),
            "rationale": brand_match_dict.get("overall_summary", "No analysis available"),
            "constraint_issues": "none",
        }

        sources = []
        for dimension in _DIMENSION_KEYS:
            dim_data = brand_match_dict.get(dimension)
            if isinstance(dim_data, dict):
                sources.append(
                    {
                        "dimension": dimension,
                        "score": dim_data.get("score", 0),
                        "summary": dim_data.get("summary", ""),
                    }
                )

        tldr_summary = evaluation.tldr_summary.strip() if evaluation.tldr_summary else ""
        if not tldr_summary:
            tldr_summary = "TLDR summary not available due to agent processing error."

        result_payload: Dict[str, Any] = {
            "job_id": job_id,
            "correlation_id": correlation_id,
            "job_intake": job_posting,
            "final": final_block,
            "pre_filter": pre_filter,
            "personas": [],
            "tradeoffs": [],
            "actions": [],
            "sources": sources,
            "overall_alignment_score": brand_match_dict.get("overall_alignment_score", 0),
            "tldr_summary": tldr_summary,
            "brand_match": brand_match_dict,
        }

        # Mirror dimension analyses at top-level for downstream transformers.
        for dimension in _DIMENSION_KEYS:
            if dimension in brand_match_dict:
                result_payload[dimension] = brand_match_dict[dimension]

        result_payload["overall_summary"] = brand_match_dict.get("overall_summary", "")

        return result_payload

    def _apply_structured_pre_filter(
        self,
        validated_job: Any,
        raw_job_posting: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply salary/date filters using structured fields instead of CrewAI."""

        salary_value = self._extract_max_salary(validated_job, raw_job_posting)
        if salary_value is not None and salary_value > 0 and salary_value < 180000:
            return {"recommend": False, "reason": "salary below 180000"}

        posted_date = self._extract_posted_date(validated_job, raw_job_posting)
        if posted_date is not None:
            now = datetime.now(timezone.utc)
            # Normalize both to naive UTC for comparison
            if posted_date.tzinfo is None:
                posted_dt = posted_date.replace(tzinfo=timezone.utc)
            else:
                posted_dt = posted_date.astimezone(timezone.utc)

            age_days = (now - posted_dt).days
            if age_days > 21:
                return {"recommend": False, "reason": "job posting older than 21 days"}

        return {"recommend": True, "reason": None}

    def _extract_max_salary(self, validated_job: Any, raw_job_posting: Dict[str, Any]) -> Optional[float]:
        """Extract maximum salary from various structured sources."""

        candidates = [
            getattr(validated_job, "highest_salary", None),
            raw_job_posting.get("highest_salary"),
            raw_job_posting.get("max_amount"),
            raw_job_posting.get("salary_max"),
        ]

        for nested_key in ("salary", "salary_info", "compensation", "salary_data"):
            nested = raw_job_posting.get(nested_key)
            if isinstance(nested, dict):
                candidates.append(nested.get("max_amount"))
                candidates.append(nested.get("salary_max"))

        for value in candidates:
            if value in (None, "", []):
                continue
            numeric = self._coerce_numeric(value)
            if numeric is not None:
                if numeric <= 0:
                    continue
                return numeric
        return None

    def _extract_posted_date(
        self,
        validated_job: Any,
        raw_job_posting: Dict[str, Any],
    ) -> Optional[datetime]:
        """Extract and parse job posting date from structured data."""

        candidates = [
            getattr(validated_job, "date_posted", None),
            raw_job_posting.get("date_posted"),
            raw_job_posting.get("posted_at"),
            raw_job_posting.get("posting_date"),
        ]

        for value in candidates:
            if value is None:
                continue
            parsed = self._parse_datetime(value)
            if parsed is not None:
                return parsed
        return None

    def _coerce_numeric(self, value: Any) -> Optional[float]:
        """Convert raw numeric inputs to float when possible."""

        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, str):
            cleaned = ''.join(ch for ch in value if ch.isdigit() or ch in {'.', '-', ','})
            if not cleaned:
                return None
            cleaned = cleaned.replace(',', '')
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse date strings or datetime objects into timezone-aware datetimes."""

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None

            # Normalize trailing Z to UTC offset
            if text.endswith('Z'):
                text = text[:-1] + '+00:00'

            for fmt in (
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f%z",
            ):
                try:
                    parsed = datetime.strptime(text, fmt)
                    if parsed.tzinfo is None:
                        return parsed.replace(tzinfo=timezone.utc)
                    return parsed
                except ValueError:
                    continue

        return None

    def _get_task_output_by_name(self, tasks_output: Any, *names: str) -> Optional[Any]:
        if not tasks_output:
            return None

        name_set = set(names)

        if isinstance(tasks_output, dict):
            for name in names:
                if name in tasks_output:
                    return tasks_output[name]
            for value in tasks_output.values():
                candidate = getattr(value, 'task_name', None)
                if candidate and candidate in name_set:
                    return value
            return None

        if isinstance(tasks_output, list):
            for entry in tasks_output:
                if entry is None:
                    continue
                task_name = self._extract_task_name(entry)
                if task_name and task_name in name_set:
                    return entry
            return None

        return None

    def _extract_task_name(self, entry: Any) -> Optional[str]:
        candidates = [
            getattr(entry, 'task_name', None),
            getattr(entry, 'name', None),
            getattr(entry, 'id', None),
        ]

        if isinstance(entry, dict):
            candidates.extend([
                entry.get('task_name'),
                entry.get('name'),
                entry.get('task'),
                entry.get('id'),
            ])

        for candidate in candidates:
            if isinstance(candidate, str) and candidate:
                return candidate
        return None

    def _build_pre_filter_section(
        self,
        pre_filter_result: Optional[Any],
        override: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if override is not None:
            return {
                "recommend": override.get("recommend", True),
                "reason": override.get("reason"),
            }

        if not pre_filter_result:
            return {"recommend": True, "reason": None}

        pre_filter_data: Optional[Dict[str, Any]] = None
        if hasattr(pre_filter_result, 'pydantic') and pre_filter_result.pydantic:
            if hasattr(pre_filter_result.pydantic, 'model_dump'):
                pre_filter_data = pre_filter_result.pydantic.model_dump()
            elif hasattr(pre_filter_result.pydantic, 'dict'):
                pre_filter_data = pre_filter_result.pydantic.dict()
        elif hasattr(pre_filter_result, 'json_dict') and pre_filter_result.json_dict:
            pre_filter_data = pre_filter_result.json_dict
        elif hasattr(pre_filter_result, 'model_dump'):
            pre_filter_data = pre_filter_result.model_dump()
        elif isinstance(pre_filter_result, dict):
            pre_filter_data = pre_filter_result

        if not pre_filter_data:
            return {"recommend": True, "reason": None}

        return {
            "recommend": pre_filter_data.get("recommend", True),
            "reason": pre_filter_data.get("reason"),
        }

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

    def _parse_crew_result(
        self,
        crew_result: Any,
        job_posting: Dict[str, Any],
        correlation_id: str,
        pre_filter_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
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

        tasks_output = crew_result.tasks_output

        brand_match_result = self._get_task_output_by_name(
            tasks_output,
            "brand_match_task",
            "brand_match",
        )
        tldr_result = self._get_task_output_by_name(
            tasks_output,
            "tldr_summary_task",
            "tldr_summary",
        )
        pre_filter_result = None if pre_filter_override else self._get_task_output_by_name(
            tasks_output,
            "pre_filter_task",
            "pre_filter",
        )

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

        # Extract TLDR summary result
        tldr_data = None
        if tldr_result:
            # Extract from TaskOutput same way as brand_match_result
            if hasattr(tldr_result, 'pydantic') and tldr_result.pydantic:
                logger.info("Extracting tldr_data from TaskOutput.pydantic")
                if hasattr(tldr_result.pydantic, 'model_dump'):
                    tldr_data = tldr_result.pydantic.model_dump()
                elif hasattr(tldr_result.pydantic, 'dict'):
                    tldr_data = tldr_result.pydantic.dict()
            elif hasattr(tldr_result, 'json_dict') and tldr_result.json_dict:
                logger.info("Extracting tldr_data from TaskOutput.json_dict")
                tldr_data = tldr_result.json_dict
            elif hasattr(tldr_result, 'model_dump'):
                logger.info("Extracting tldr_data from direct Pydantic model")
                tldr_data = tldr_result.model_dump()
            elif isinstance(tldr_result, dict):
                logger.info("tldr_result is already a dict")
                tldr_data = tldr_result
            else:
                logger.warning(f"Cannot extract tldr_data from type: {type(tldr_result)}")
                tldr_data = {}
        else:
            logger.warning("No TLDR result found in crew output - this may indicate an agent failure")
            tldr_data = {}

        if tldr_data:
            logger.info(f"Successfully extracted tldr_data: {tldr_data}")
        else:
            logger.warning("TLDR data extraction resulted in empty or None result")

        # Extract pre-filter result
        # Convert to worker-expected format
        final = {
            "recommend": brand_data.get("recommend", False),
            "confidence": brand_data.get("confidence", "low"),
            "rationale": brand_data.get("overall_summary", "No analysis available"),
            "constraint_issues": brand_data.get("constraint_issues", "none")
        }

        pre_filter = self._build_pre_filter_section(pre_filter_result, pre_filter_override)

        # Extract individual dimension analyses for sources array
        sources = []
        dimension_names = ["north_star", "trajectory_mastery", "values_compass",
                          "lifestyle_alignment", "compensation_philosophy"]

        for dim_name in dimension_names:
            if dim_name in brand_data and isinstance(brand_data[dim_name], dict):
                dim_data = brand_data[dim_name]
                sources.append({
                    "dimension": dim_name,
                    "score": dim_data.get("score", 0),
                    "summary": dim_data.get("summary", "")
                })

        # Calculate overall_alignment_score if not provided
        overall_score = brand_data.get("overall_alignment_score", 0)
        if overall_score == 0 or overall_score is None:
            # Fallback: calculate from individual dimension scores
            overall_score = self._calculate_fallback_alignment_score(brand_data)
            logger.info(f"Calculated fallback overall_alignment_score: {overall_score}")

        # Extract TLDR summary for inclusion in response
        tldr_summary = tldr_data.get("tldr_summary", "") if tldr_data else ""
        if not tldr_summary:
            logger.warning("No TLDR summary available in tldr_data - providing default message")
            tldr_summary = "TLDR summary not available due to agent processing error."

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
            "sources": sources,
            "overall_alignment_score": overall_score,
            "tldr_summary": tldr_summary  # TLDR summary for quick human review
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
                # Preserve any previously calculated score when brand_match block is unavailable
                existing_score = transformed.get("overall_alignment_score")
                if existing_score is None:
                    transformed["overall_alignment_score"] = analysis_result.get("overall_alignment_score", 0)
                else:
                    transformed["overall_alignment_score"] = existing_score

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
        Uses 5 core dimensions with redistributed weights (removed constraints, purpose_impact, industry_focus, company_filters).
        """
        try:
            dimensions = [
                "north_star", "trajectory_mastery", "values_compass",
                "lifestyle_alignment", "compensation_philosophy"
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

            # Redistributed weights for 5 core dimensions (total = 1.00)
            # Compensation and trajectory remain most important
            weights = {
                "compensation_philosophy": 0.30,  # Increased from 0.20
                "trajectory_mastery": 0.30,       # Increased from 0.18
                "north_star": 0.20,               # Increased from 0.15
                "values_compass": 0.15,           # Increased from 0.10
                "lifestyle_alignment": 0.05,      # Decreased from 0.08
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
