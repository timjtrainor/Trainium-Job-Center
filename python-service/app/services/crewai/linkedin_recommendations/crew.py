"""
LinkedIn Recommendations CrewAI implementation.

This crew fetches personalized job recommendations from LinkedIn using dynamically loaded MCP tools.
"""
import json
from collections.abc import Mapping
from json import JSONDecodeError
from threading import Lock
from typing import Any, Dict, Optional

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from loguru import logger

from ..base import get_linkedin_tools, test_linkedin_mcp_connection_sync


_cached_crew: Optional[Crew] = None
_crew_lock = Lock()

# No longer using report schema - expecting JSON array directly

@CrewBase
class LinkedInRecommendationsCrew:
    """
    LinkedIn Recommendations crew for fetching personalized job recommendations.

    This crew uses dynamically loaded LinkedIn MCP tools to retrieve
    algorithmically suggested jobs and formats them for database persistence.
    """
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Initialize crew with LinkedIn MCP tool integration."""
        # Test LinkedIn MCP connection on initialization
        connection_status = test_linkedin_mcp_connection_sync()
        if connection_status.get("success"):
            logger.info(f"LinkedIn MCP connection successful. Found {len(connection_status.get('linkedin_tools', []))} LinkedIn tools")
            if connection_status.get("missing_tools"):
                logger.warning(f"Missing LinkedIn tools: {connection_status.get('missing_tools')}")
        else:
            logger.error(f"LinkedIn MCP connection failed: {connection_status.get('error')}")
        
        # Load LinkedIn tools dynamically
        self._linkedin_tools = get_linkedin_tools()
        logger.info(f"Loaded {len(self._linkedin_tools)} LinkedIn MCP tools for recommendations crew")
        
        # CRITICAL: Fail if no LinkedIn tools are available to prevent hallucination
        if not self._linkedin_tools:
            error_msg = "CRITICAL: No LinkedIn MCP tools loaded. Agents will hallucinate data without tools."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    @agent
    def linkedin_recommendations_fetcher(self) -> Agent:
        """Specialist agent for fetching LinkedIn job recommendations with all LinkedIn MCP tools."""
        return Agent(
            config=self.agents_config["linkedin_recommendations_fetcher"],  # type: ignore[index]
            tools=self._linkedin_tools,  # Dynamically provide all LinkedIn tools
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
    """Execute LinkedIn recommendations fetching with comprehensive logging and validation."""

    # Test LinkedIn MCP connection before execution
    connection_status = test_linkedin_mcp_connection_sync()
    if not connection_status.get("success"):
        logger.error(f"LinkedIn MCP connection failed before recommendations fetch: {connection_status.get('error')}")
        return {
            "success": False,
            "error": f"LinkedIn MCP connection failed: {connection_status.get('error')}",
            "connection_status": connection_status
        }

    logger.info(f"LinkedIn recommendations starting with {len(connection_status.get('linkedin_tools', []))} available LinkedIn tools")
    
    # CRITICAL: Check if any LinkedIn tools were actually found
    if not connection_status.get("linkedin_tools"):
        error_msg = "CRITICAL: No LinkedIn MCP tools available. Cannot fetch authentic LinkedIn data. Check MCP gateway connection."
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "connection_status": connection_status
        }
    
    try:
        crew = get_linkedin_recommendations_crew()
    except RuntimeError as e:
        logger.error(f"Failed to initialize LinkedIn recommendations crew: {e}")
        return {
            "success": False,
            "error": str(e),
            "connection_status": connection_status
        }
    
    inputs = {}  # No specific inputs needed for recommendations
    
    try:
        logger.info("Executing LinkedIn recommendations crew")
        raw_result = crew.kickoff(inputs=inputs)
        
        # Validate result format and data authenticity
        normalized_result = normalize_linkedin_recommendations_output(raw_result)
        
        # Enhanced logging for result validation
        if normalized_result.get("recommended_jobs"):
            jobs_count = len(normalized_result["recommended_jobs"])
            logger.info(f"LinkedIn recommendations completed successfully: {jobs_count} jobs found")
            
            # Validate authentic LinkedIn data structure
            sample_job = normalized_result["recommended_jobs"][0] if jobs_count > 0 else {}
            
            # Check for authentic LinkedIn data characteristics
            if sample_job:
                has_linkedin_url = "linkedin.com" in str(sample_job.get("job_url", ""))
                has_source_raw = sample_job.get("source_raw") is not None
                
                if has_linkedin_url:
                    logger.info("✅ Authentic LinkedIn data detected - contains LinkedIn URLs")
                else:
                    logger.warning("⚠️ Potential hallucinated data - missing LinkedIn URLs")
                    
                if has_source_raw:
                    logger.info("✅ Source data preserved - original LinkedIn response stored")
                else:
                    logger.warning("⚠️ Source data missing - no original LinkedIn response")
                    
                # Check for sparse data (typical of LinkedIn API)
                null_fields = sum(1 for v in sample_job.values() if v is None or v == "")
                total_fields = len(sample_job)
                if null_fields > total_fields * 0.3:  # More than 30% null/empty
                    logger.info(f"✅ Sparse data pattern detected ({null_fields}/{total_fields} null) - typical of LinkedIn API")
                else:
                    logger.warning("⚠️ Suspiciously complete data - may be hallucinated")
                    
                # Check for authentic LinkedIn URL patterns (long collection URLs)
                if "collections/recommended" in str(sample_job.get("job_url", "")):
                    logger.info("✅ Authentic LinkedIn collection URL detected")
                else:
                    logger.warning("⚠️ Missing authentic LinkedIn collection URL pattern")
                    
        else:
            logger.warning("LinkedIn recommendations completed but no jobs found in result")
            
        return normalized_result
        
    except Exception as e:
        logger.error(f"LinkedIn recommendations execution failed: {str(e)}")
        return {
            "success": False,
            "error": f"Recommendations fetch failed: {str(e)}",
            "recommended_jobs": [],
            "total_recommendations": 0
        }