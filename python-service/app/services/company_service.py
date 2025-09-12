import json
import re
from app.services.crewai.research_company.crew import get_research_company_crew
from app.schemas.company import CompanyReport


def generate_company_report(company_name: str) -> CompanyReport:
    """Run CrewAI and return parsed JSON report."""
    crew = get_research_company_crew()
    result = crew.kickoff(inputs={"company_name": company_name})
    raw_output = getattr(result, "raw", str(result))
    match = re.search(r"\{.*\}$", raw_output, re.S)
    if not match:
        raise ValueError("Invalid JSON output from CrewAI")
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON output from CrewAI") from exc
    return CompanyReport(**data)
