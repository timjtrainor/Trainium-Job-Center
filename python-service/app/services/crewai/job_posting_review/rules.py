"""Data models and utilities for job posting evaluation. Business logic remains in CrewAI agents."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import hashlib
from datetime import datetime


class JobPostingInput(BaseModel):
    """Input validation model for job postings."""

    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: Optional[str] = Field(None, description="Job description")
    highest_salary: Optional[float] = Field(None, description="Highest salary offered")
    lowest_salary: Optional[float] = Field(None, description="Lowest salary offered")
    date_posted: Optional[str] = Field(None, description="Job posting date")
    seniority: Optional[str] = Field(None, description="Seniority level")
    job_type: Optional[str] = Field(None, description="Job type (remote, hybrid, in-person)")
    location: Optional[str] = Field(None, description="Job location")
    link: Optional[str] = Field(None, description="Job posting URL")


class PersonaAnalysis(BaseModel):
    """Structure for individual agent persona analysis."""

    id: str = Field(..., description="Agent/persona identifier")
    recommend: bool = Field(..., description="Recommendation boolean")
    reason: str = Field(..., description="Brief reasoning")


class EvaluationSummary(BaseModel):
    """Summary of complete job evaluation."""

    recommend: bool = Field(..., description="Final recommendation")
    rationale: str = Field(..., description="Comprehensive rationale")
    confidence: str = Field(..., description="Confidence level: low/medium/high")


def generate_job_id(job_posting: Dict[str, Any]) -> str:
    """Generate deterministic job ID from posting content."""
    content = str(sorted(job_posting.items()))
    return f"job_{hashlib.md5(content.encode()).hexdigest()[:8]}"


def validate_job_posting(job_posting: Dict[str, Any]) -> JobPostingInput:
    """Validate and normalize job posting data."""
    try:
        return JobPostingInput(**job_posting)
    except Exception as e:
        raise ValueError(f"Invalid job posting data: {e}")


def get_current_iso_timestamp() -> str:
    """Get current timestamp in ISO format for correlation."""
    return datetime.now().isoformat()


def deduplicate_items(items: List[str]) -> List[str]:
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def clean_llm_json_response(raw_output: str) -> str:
    """
    Clean LLM response to extract pure JSON, handling common formatting issues.
    Designed for Gemma3, Phi3, and other models that wrap JSON in markdown.
    """
    import re

    # Strip whitespace
    cleaned = raw_output.strip()

    # Remove markdown code blocks (```json ... ``` or ``` ... ```)
    if cleaned.startswith('```'):
        # Find the content between code fences
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()

    # Remove any remaining markdown artifacts
    cleaned = re.sub(r'^```json\s*', '', cleaned)
    cleaned = re.sub(r'^```\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)

    # Remove any leading/trailing text before/after JSON
    # Look for the first { and last }
    json_start = cleaned.find('{')
    json_end = cleaned.rfind('}')

    if json_start != -1 and json_end != -1 and json_end > json_start:
        cleaned = cleaned[json_start:json_end + 1]

    return cleaned.strip()


def extract_json_from_crew_output(raw_output: str) -> Dict[str, Any]:
    """Extract JSON payload from CrewAI agent output."""
    import json
    import re

    # First, clean the response (handles markdown wrapping)
    cleaned_output = clean_llm_json_response(raw_output)

    # Try direct JSON parsing on cleaned output
    try:
        return json.loads(cleaned_output)
    except json.JSONDecodeError:
        pass

    # Fallback: Try direct parsing on original (for already-clean JSON)
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        pass

    # Look for JSON in markdown code blocks (legacy support)
    json_match = re.search(r'```(?:json)?\s*\n?(\{.*?\})\s*\n?```', raw_output, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Look for bare JSON object
    json_match = re.search(r'(\{.*\})', raw_output, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Return a basic structure if parsing fails
    return {"raw_output": raw_output, "parsing_error": True}
