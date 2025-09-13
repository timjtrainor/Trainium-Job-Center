import json
import re

from app.services.crewai.research_company.crew import get_research_company_crew
from app.schemas.company import CompanyReport

def generate_company_report(company_name: str) -> CompanyReport:
    """Run CrewAI and return parsed JSON report."""
    crew = get_research_company_crew()
    result = crew.kickoff(inputs={"company_name": company_name})
    raw_output = getattr(result, "raw", str(result))

    # Prefer fenced JSON code blocks; fall back to first JSON object.
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_output, re.DOTALL)
    if not match:
        match = re.search(r"(\{.*\})", raw_output, re.DOTALL)
    if not match:
        raise ValueError("No JSON payload found in CrewAI output")

    json_str = match.group(1)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON in CrewAI output") from exc

    return CompanyReport(**data)
