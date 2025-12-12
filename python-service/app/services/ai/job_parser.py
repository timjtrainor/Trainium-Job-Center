import json
import re
from typing import Optional
from loguru import logger

from ...core.config import get_settings
from .llm_clients import LLMRouter
from ...schemas.job_parsing import JobParseResponse


class JobParser:
    def __init__(self):
        settings = get_settings()
        # Default to a capable model if not specified in settings, but LLMRouter handles preferences
        self.router = LLMRouter(preferences=settings.llm_preference)

    def parse_job_text(self, text: str) -> JobParseResponse:
        """
        Parse raw job text to extract structured data using LLM.
        """
        prompt = f"""
        You are an expert job market analyst. Your task is to extract structured information from the provided raw job posting text.

        Extract the following fields:
        1. title: The specific job title.
        2. company_name: The name of the hiring company.
        3. location: The job location (City, State/Country).
        4. salary_min: The minimum salary number (numeric only, no symbols). If hourly, convert to yearly if possible (assume 2000 hrs), otherwise keep as is.
        5. salary_max: The maximum salary number (numeric only).
        6. salary_currency: The currency code (e.g., USD, EUR, GBP). Default to USD if not specified but looks like dollars.
        7. remote_status: One of "Remote", "Hybrid", "On-site". Infer from text if not explicit.
        8. date_posted: The posting date in YYYY-MM-DD format if available.
        9. cleaned_description: The core job description text, stripped of navigation menus, headers, footers, and irrelevant side-bar content.

        Return the result as a single valid JSON object. Do not include markdown formatting like ```json ... ```.

        If a field cannot be found, set it to null.

        RAW TEXT:
        {text[:15000]}  # Truncate to avoid token limits if extremely long

        JSON OUTPUT:
        """

        try:
            response_text = self.router.generate(prompt)

            # Clean up potential markdown formatting
            clean_text = self._clean_json_string(response_text)

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
            logger.error(f"Failed to decode JSON from LLM response: {e}. Response: {response_text}")
            # Fallback: try to just return the original text as description
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


# Global parser instance
_job_parser: Optional[JobParser] = None


def get_job_parser() -> JobParser:
    """Get the global job parser instance."""
    global _job_parser
    if _job_parser is None:
        _job_parser = JobParser()
    return _job_parser
