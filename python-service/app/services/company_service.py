import json
from app.services.crewai.research_company.crew import get_research_company_crew

def generate_company_report(company_name: str) -> dict:
    """Run CrewAI and return parsed JSON report."""
    crew = get_research_company_crew()
    result = crew.kickoff(inputs={"company_name": company_name})
    return json.loads(result)