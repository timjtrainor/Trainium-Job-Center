"""
LinkedIn Recommendations CrewAI implementation.

This crew fetches personalized job recommendations from LinkedIn using the get_recommended_jobs MCP tool.
"""
import json
from collections.abc import Mapping
from json import JSONDecodeError
from threading import Lock
from typing import Any, Dict, Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew


_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

# No longer using report schema - expecting JSON array directly

@CrewBase
class LinkedInRecommendationsCrew:
    """
    LinkedIn Recommendations crew for fetching personalized job recommendations.

    This crew uses the LinkedIn MCP 'get_recommended_jobs' tool to retrieve
    algorithmically suggested jobs and formats them for database persistence.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def linkedin_recommendations_fetcher(self) -> Agent:
        """Specialist agent for fetching LinkedIn job recommendations."""
        return Agent(
            config=self.agents_config["linkedin_recommendations_fetcher"],  # type: ignore[index]
        )


    @task
    def fetch_recommended_jobs(self) -> Task:
        """Fetch personalized job recommendations from LinkedIn."""
        return Task(
            config=self.tasks_config["fetch_recommended_jobs"],  # type: ignore[index]
            agent=self.linkedin_recommendations_fetcher(),
        )


    @crew
    def crew(self) -> Crew:
        """Assemble the complete LinkedIn recommendations crew."""
        return Crew(
            agents=[
                self.linkedin_recommendations_fetcher()
            ],
            tasks=[
                self.fetch_recommended_jobs()
            ],
            process=Process.sequential,
            verbose=True,
        )


def get_linkedin_recommendations_crew() -> Crew:
    """Factory function with singleton pattern for crew instances."""
    global _cached_crew
    if _cached_crew is None:
        with _crew_lock:
            if _cached_crew is None:
                _cached_crew = LinkedInRecommendationsCrew().crew()
    assert _cached_crew is not None
    return _cached_crew


def _coerce_to_dict(candidate: Any) -> Optional[Dict[str, Any]]:
    """Attempt to convert various CrewAI output payloads into a dictionary."""

    if candidate is None:
        return None

    if isinstance(candidate, Mapping):
        return dict(candidate)

    if isinstance(candidate, str):
        stripped = candidate.strip()
        if not stripped:
            return None

        try:
            parsed = json.loads(stripped)
        except JSONDecodeError:
            return None

        if isinstance(parsed, Mapping):
            return dict(parsed)

        # Preserve non-mapping JSON payloads for downstream inspection.
        return {"data": parsed}

    return None


def normalize_linkedin_recommendations_output(result: Any) -> Dict[str, Any]:
    """Normalize CrewAI outputs into a dictionary for consistent consumption."""
    
    # Try to parse as JSON array first (new format)
    if isinstance(result, str):
        try:
            parsed = json.loads(result.strip())
            if isinstance(parsed, list):
                # Return as expected format with job array
                return {
                    "success": True,
                    "recommended_jobs": parsed,
                    "total_recommendations": len(parsed)
                }
        except JSONDecodeError:
            pass
    
    # Handle raw result attributes
    for attribute in ("raw", "output", "value"):
        if hasattr(result, attribute):
            attr_value = getattr(result, attribute)
            if isinstance(attr_value, str):
                try:
                    parsed = json.loads(attr_value.strip())
                    if isinstance(parsed, list):
                        return {
                            "success": True,
                            "recommended_jobs": parsed,
                            "total_recommendations": len(parsed)
                        }
                except JSONDecodeError:
                    continue
    
    # Fallback for other formats
    normalized = _coerce_to_dict(result)
    if normalized is not None:
        return normalized

    return {"success": False, "error": "Could not parse recommendations output"}


def run_linkedin_recommendations() -> Dict[str, Any]:
    """Execute LinkedIn recommendations fetching using the shared crew instance."""

    crew = get_linkedin_recommendations_crew()
    inputs = {}  # No specific inputs needed for recommendations
    raw_result = crew.kickoff(inputs=inputs)
    return normalize_linkedin_recommendations_output(raw_result)