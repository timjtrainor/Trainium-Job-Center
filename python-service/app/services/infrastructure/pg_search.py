"""PostgreSQL search tool for CrewAI agents."""

from typing import List, Dict, Any
from loguru import logger

from .postgrest import get_postgrest_service


class PGSearchTool:
    """Simple search tool using PostgREST service."""

    def __init__(self):
        self.service = get_postgrest_service()

    async def search_jobs(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search jobs table for titles matching query.

        Args:
            query: Text to search in job titles.
            limit: Maximum number of results to return.
        """
        try:
            if not self.service.client:
                await self.service.initialize()

            params = {
                "title": f"ilike.%{query}%",
                "limit": str(limit),
            }
            response = await self.service.client.get("/jobs", params=params)
            if response.status_code == 200:
                return response.json()
            logger.error(f"PostgREST search failed: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"PostgREST search error: {e}")
        return []


def get_pg_search_tool() -> PGSearchTool:
    """Create a new PGSearchTool instance."""
    return PGSearchTool()


