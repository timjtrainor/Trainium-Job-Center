"""Single-call evaluator for job posting review with cached prompt sections."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import chromadb
from loguru import logger
from openai import OpenAI

from ....core.config import resolve_api_key
from models.creaii_schemas import (
    BrandDimensionAnalysis,
    BrandDimensionSynthesis,
    BrandMatchComplete,
)


_DIMENSION_WEIGHTS = {
    "compensation_philosophy": 0.30,
    "trajectory_mastery": 0.30,
    "north_star": 0.20,
    "values_compass": 0.15,
    "lifestyle_alignment": 0.05,
}

_DIMENSIONS = list(_DIMENSION_WEIGHTS.keys())


_DIMENSION_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "summary": {
            "type": "string",
            "minLength": 10,
            "maxLength": 250,
        },
    },
    "required": ["score", "summary"],
    "additionalProperties": False,
}


_RESPONSE_SCHEMA = {
    "name": "BrandDimensionSynthesis",
    "schema": {
        "type": "object",
        "properties": {
            dim: _DIMENSION_SCHEMA for dim in _DIMENSIONS
        },
        "required": _DIMENSIONS + ["overall_summary", "tldr_summary"],
        "additionalProperties": False,
    },
}

_RESPONSE_SCHEMA["schema"]["properties"].update(
    {
        "overall_summary": {
            "type": "string",
            "minLength": 20,
            "maxLength": 600,
        },
        "tldr_summary": {
            "type": "string",
            "minLength": 20,
            "maxLength": 400,
        },
    }
)


_SYSTEM_PROMPT = (
    "You are a senior career strategist who delivers structured assessments. "
    "Always follow the scoring rubric and respond with strict JSON only."
)

_RUBRIC_PROMPT = """
SCORING RUBRIC (1-5):
- 1 → Critical mismatch; 2 → Insufficient data or notable concerns; 3 → Acceptable baseline; 4 → Strong alignment; 5 → Exceptional alignment.

DIMENSION INTERPRETATIONS:
- north_star: long-term vision, mission fit, impact trajectory.
- trajectory_mastery: skill development path, technical challenge, learning velocity.
- values_compass: culture, leadership style, collaboration norms.
- lifestyle_alignment: schedule, flexibility, workload, region expectations.
- compensation_philosophy: salary, equity, benefits, total rewards philosophy.

OUTPUT FIELDS:
- Provide one JSON object containing the five dimension objects, an overall_summary (5–7 sentences referencing evidence from each dimension), and a concise tldr_summary (3–5 bullets or <=3 sentences).
- Summaries must cite relevant evidence from the job posting and the brand profile.
- Never add extra fields or free text.
""".strip()


@dataclass
class SingleAgentResult:
    """Container for single-call evaluation output."""

    brand_match: BrandMatchComplete
    tldr_summary: str


class BrandMatchSingleAgentEvaluator:
    """Evaluates a job posting in a single LLM call with cached prompt sections."""

    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or os.getenv("JOB_REVIEW_SINGLE_AGENT_MODEL", "gpt-5-nano")
        api_key = resolve_api_key("openai")
        self._client: Optional[OpenAI] = OpenAI(api_key=api_key) if api_key else None
        self._brand_profile_payload: Optional[str] = None

    def is_available(self) -> bool:
        """Return True when the OpenAI client is ready."""
        return self._client is not None

    async def evaluate(self, job_posting: Dict[str, Any]) -> SingleAgentResult:
        """Run the single-call evaluation pipeline."""
        if not self.is_available():
            raise RuntimeError("OpenAI client unavailable for single agent evaluator")

        payload = await asyncio.to_thread(self._run_sync, job_posting)
        return payload

    # --- Internal helpers -------------------------------------------------

    def _run_sync(self, job_posting: Dict[str, Any]) -> SingleAgentResult:
        brand_payload = self._get_cached_brand_profile()
        request_inputs = self._build_request_inputs(brand_payload, job_posting)
        response = self._client.responses.create(  # type: ignore[union-attr]
            model=self.model,
            input=request_inputs,
            temperature=0.2,
            max_output_tokens=1200,
            response_format={"type": "json_schema", "json_schema": _RESPONSE_SCHEMA},
        )

        content_text = self._extract_response_text(response)
        logger.debug(f"Single-agent raw response: {content_text}")
        try:
            parsed = json.loads(content_text)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            logger.error(f"Failed to parse LLM response as JSON: {exc}\n{content_text}")
            raise

        synthesis = BrandDimensionSynthesis.model_validate(parsed)
        brand_match = self._to_brand_match(synthesis)
        return SingleAgentResult(brand_match=brand_match, tldr_summary=synthesis.tldr_summary)

    def _extract_response_text(self, response: Any) -> str:
        """Extract text content from a Responses API result."""
        chunks = []
        for output in getattr(response, "output", []) or []:
            for item in getattr(output, "content", []) or []:
                if hasattr(item, "text") and item.text:
                    chunks.append(item.text)
                elif hasattr(item, "json") and item.json:
                    chunks.append(json.dumps(item.json))
        if not chunks and hasattr(response, "output_text"):
            return response.output_text
        return "".join(chunks)

    def _get_cached_brand_profile(self) -> str:
        if self._brand_profile_payload is not None:
            return self._brand_profile_payload

        profile = {dim: self._load_dimension(dim) for dim in _DIMENSIONS}
        serialized = json.dumps(
            {"brand_profile": profile, "version": "v1"},
            sort_keys=True,
            separators=(",", ":"),
        )
        self._brand_profile_payload = serialized
        logger.info("Cached brand profile payload for single-agent evaluator")
        return serialized

    def _load_dimension(self, dimension: str) -> str:
        """Fetch dimension-specific knowledge from ChromaDB."""
        try:
            client = chromadb.HttpClient(host="chromadb", port=8001)
            collection = client.get_collection("career_brand")
            results = collection.get(
                where={"dimension": dimension},
                limit=50,
                include=["documents", "metadatas"],
            )
            documents = results.get("documents") if results else None
            metadatas = results.get("metadatas") if results else None
            if not documents:
                logger.warning(f"No documents found for dimension '{dimension}'")
                return f"No branded knowledge available for {dimension}."

            paired = list(zip(documents, metadatas or []))
            paired.sort(key=lambda item: item[1].get("seq", 0) if isinstance(item[1], dict) else 0)
            return "\n\n".join(doc for doc, _ in paired if doc)
        except Exception as exc:
            logger.warning(f"Failed to load dimension '{dimension}' from ChromaDB: {exc}")
            return f"Knowledge unavailable for {dimension} due to retrieval error: {exc}"

    def _build_request_inputs(
        self,
        brand_payload: str,
        job_posting: Dict[str, Any],
    ) -> Any:
        job_payload = json.dumps(
            {"job_posting": job_posting},
            sort_keys=True,
            separators=(",", ":"),
        )

        return [
            {
                "role": "system",
                "content": [{"type": "text", "text": _SYSTEM_PROMPT}],
                "cache_control": {"type": "ephemeral"},
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": _RUBRIC_PROMPT}],
                "cache_control": {"type": "ephemeral"},
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": brand_payload,
                    }
                ],
                "cache_control": {"type": "ephemeral"},
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": job_payload}],
            },
        ]

    def _to_brand_match(self, synthesis: BrandDimensionSynthesis) -> BrandMatchComplete:
        dimension_scores = {
            name: getattr(synthesis, name) for name in _DIMENSIONS
        }

        weighted_sum = 0.0
        total_weight = 0.0
        for name, analysis in dimension_scores.items():
            converted = self._convert_five_point_score(analysis.score)
            weight = _DIMENSION_WEIGHTS[name]
            weighted_sum += converted * weight
            total_weight += weight

        overall_score = round(weighted_sum / total_weight, 2) if total_weight else 0.0
        confidence = self._confidence_from_score(overall_score)
        recommend = overall_score >= 5.0

        return BrandMatchComplete(
            north_star=dimension_scores["north_star"],
            trajectory_mastery=dimension_scores["trajectory_mastery"],
            values_compass=dimension_scores["values_compass"],
            lifestyle_alignment=dimension_scores["lifestyle_alignment"],
            compensation_philosophy=dimension_scores["compensation_philosophy"],
            overall_alignment_score=overall_score,
            overall_summary=synthesis.overall_summary,
            recommend=recommend,
            confidence=confidence,
        )

    def _convert_five_point_score(self, score: int) -> float:
        return float(2 + (score - 1) * 2)

    def _confidence_from_score(self, score: float) -> str:
        if score <= 4.0:
            return "low"
        if score <= 6.0:
            return "medium"
        return "high"
