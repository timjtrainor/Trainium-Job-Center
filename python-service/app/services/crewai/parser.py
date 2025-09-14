import json
import re
from typing import Any, Dict


def _find_json_block(text: str) -> str:
    """Extract the first JSON object from a text blob.

    Prefers fenced code blocks but falls back to first JSON-like braces.
    Raises ValueError if no JSON is found.
    """
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1)

    brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace_match:
        return brace_match.group(1)

    raise ValueError("No JSON payload found in crew output")


def _has_score_field(obj: Any) -> bool:
    """Recursively check for any key containing 'score'."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if "score" in key.lower():
                return True
            if _has_score_field(value):
                return True
    elif isinstance(obj, list):
        return any(_has_score_field(item) for item in obj)
    return False


def parse_crew_result(raw_output: str) -> Dict[str, Any]:
    """Parse and validate CrewAI output.

    Args:
        raw_output: Raw string from `crew.kickoff`.

    Returns:
        Structured dictionary with required keys and separate metrics under `data`.

    Raises:
        ValueError: If JSON is missing or required fields are absent.
    """
    json_str = _find_json_block(raw_output)
    data = json.loads(json_str)

    required_keys = {"final", "personas", "tradeoffs", "actions", "sources"}
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f"Missing required keys in crew output: {', '.join(missing)}")
    if not _has_score_field(data):
        raise ValueError("No score fields present in crew output")

    final = data.get("final", {})
    rationale = str(final.get("rationale", ""))
    summary = rationale.split("\n")[0][:200]
    final["rationale"] = summary

    standard_keys = {"final", "personas", "tradeoffs", "actions", "sources"}
    metrics = {k: v for k, v in data.items() if k not in standard_keys}

    structured = {k: data[k] for k in data if k in standard_keys}
    structured["data"] = metrics
    structured["final"] = final
    return structured
