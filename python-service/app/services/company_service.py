import json
from app.services.crewai.research_company.crew import get_research_company_crew
from app.schemas.company import CompanyReport
from pydantic import ValidationError

def generate_company_report(company_name: str) -> CompanyReport:
    """Run CrewAI and return parsed JSON report."""
    crew = get_research_company_crew()
    result = crew.kickoff(inputs={"company_name": company_name})
    raw_output = getattr(result, "raw", str(result))
    start = raw_output.find("{")
    end = raw_output.rfind("}")
    if start == -1 or end == -1 or start > end:
        raise ValueError("Invalid JSON output from CrewAI")
    try:
        data = json.loads(raw_output[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON output from CrewAI") from exc
    recent_news = data.get("recent_news")
    if isinstance(recent_news, dict):
        data["recent_news"] = list(recent_news.values())
    elif recent_news is not None and not isinstance(recent_news, list):
        raise ValueError("recent_news must be a dict or list")
    try:
        return CompanyReport(**data)
    except ValidationError as exc:
        raise ValueError(f"Invalid company report: {exc}") from exc
