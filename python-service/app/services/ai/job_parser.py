import json
import re
from typing import Optional
from loguru import logger
import litellm

from ...schemas.job_parsing import JobParseResponse
from .ai_service import ai_service

class JobParser:
    def __init__(self):
        # Use fast, lightweight model for parsing
        # Try to resolvealias, fallback to gemini-1.5-flash
        self.model = ai_service.get_model_for_alias("fast-response") or "gemini/gemini-1.5-flash"

    def parse_job_text(self, text: str) -> JobParseResponse:
        """
        Parse raw job text to extract structured data using LLM via Langfuse prompt.
        """
        try:
            # Execute managed prompt from Langfuse
            data = ai_service.execute_prompt(
                prompt_name="EXTRACT_DETAILS_FROM_PASTE",
                variables={
                    "JOB_DESCRIPTION": text[:20000] # Increased limit for safety
                },
                json_schema={"type": "object"}, # Enforce JSON output
                label="production"
            )

            # If execute_prompt returns string (it might if json_schema wasn't strictly enforced by provider), parse it
            if isinstance(data, str):
                clean_text = self._clean_json_string(data)
                data = json.loads(clean_text)

            # Post-processing
            return JobParseResponse(
                title=data.get("title"),
                company_name=data.get("company_name"),
                description=data.get("cleaned_description") or text, # Fallback to original text if empty
                location=data.get("location"),
                salary_min=self._parse_float(data.get("salary_min")),
                salary_max=self._parse_float(data.get("salary_max")),
                salary_currency=data.get("salary_currency", "USD"),
                remote_status=self._normalize_remote_status(data.get("remote_status")),
                date_posted=data.get("date_posted")
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from LLM response: {e}")
            return JobParseResponse(description=text)
        except Exception as e:
            logger.error(f"Error parsing job text: {e}")
            return JobParseResponse(description=text)

    def _clean_json_string(self, text: str) -> str:
        """Remove markdown code blocks and whitespace."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _parse_float(self, value) -> Optional[float]:
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove currency symbols and commas
                clean = re.sub(r'[^\d.]', '', value)
                return float(clean)
        except ValueError:
            return None
        return None

    def _normalize_remote_status(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        value = value.lower()
        if "remote" in value:
            return "Remote"
        if "hybrid" in value:
            return "Hybrid"
        if "site" in value or "office" in value:
            return "On-site"
        return None
