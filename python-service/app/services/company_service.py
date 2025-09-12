import json
from app.services.crewai.research_company.crew import get_research_company_crew


def generate_company_report(company_name: str) -> dict:
    """Run CrewAI and return parsed JSON report."""
    crew = get_research_company_crew()
    result = crew.kickoff(inputs={"company_name": company_name})
    raw_output = getattr(result, "raw", str(result))
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON output from CrewAI") from exc
