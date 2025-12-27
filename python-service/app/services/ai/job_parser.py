import json
import re
from typing import Optional
from loguru import logger

from .llm_clients import LLMRouter
from ...schemas.job_parsing import JobParseResponse

class JobParser:
    def __init__(self):
        # Use fast, lightweight models for parsing task to ensure low latency
        # prioritizing Gemini 1.5 Flash as requested for speed
        self.router = LLMRouter(preferences="gemini:gemini-1.5-flash,openai:gpt-4o-mini,ollama:llama3")

    def parse_job_text(self, text: str) -> JobParseResponse:
        """
        Parse raw job text to extract structured data using LLM.
        """
        prompt = f"""Extract structured data from the job posting below into a valid JSON object.

Fields:
- title: Job title
- company_name: Company name
- location: Location (City, State)
- salary_min: Min salary (number, annual)
- salary_max: Max salary (number, annual)
- salary_currency: Currency code (default "USD")
- remote_status: "Remote", "Hybrid", "On-site", or null
- date_posted: "YYYY-MM-DD" or null
- cleaned_description: The EXACT copy of the job description text provided, but with UI noise (navigation menus, headers, footers, cookie notices, "apply now" buttons, etc.) removed. DO NOT summarize, rewrite, or shorten the description text itself. Keep all bullet points, formatting, and sections exactly as they are.

Return ONLY JSON.

TEXT:
{text[:15000]}
"""

        response_text = ""
        try:
            response_text = self.router.generate(
                prompt,
                temperature=0.0,  # Deterministic for faster/consistent parsing
                max_tokens=2048   # Limit output to prevent runaways
            )

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
