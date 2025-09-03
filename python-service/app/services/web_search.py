"""
Web search tool for AI agents using Tavily API.

This module provides web search capabilities for CrewAI agents, allowing them
to gather real-time information from the web to enhance their analysis and
decision-making.
"""

from typing import Dict, List, Any, Optional
from loguru import logger

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

from ..core.config import resolve_api_key


class WebSearchTool:
    """Web search tool using Tavily API."""
    
    def __init__(self):
        """Initialize web search client."""
        self.api_key = resolve_api_key("tavily")
        if TavilyClient and self.api_key:
            self.client = TavilyClient(api_key=self.api_key)
        else:
            self.client = None
            if not self.api_key:
                logger.warning("Tavily API key not configured - web search disabled")
            if not TavilyClient:
                logger.warning("Tavily client not available - web search disabled")
    
    def is_available(self) -> bool:
        """Check if web search is available."""
        return self.client is not None
    
    def search(
        self, 
        query: str, 
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform web search and return results.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            search_depth: "basic" or "advanced" search depth
            include_domains: List of domains to include in search
            exclude_domains: List of domains to exclude from search
            
        Returns:
            List of search results with title, url, content, and score
        """
        if not self.is_available():
            logger.warning("Web search not available, returning empty results")
            return []
        
        try:
            search_kwargs = {
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth
            }
            
            if include_domains:
                search_kwargs["include_domains"] = include_domains
            if exclude_domains:
                search_kwargs["exclude_domains"] = exclude_domains
            
            response = self.client.search(**search_kwargs)
            
            # Extract relevant information from response
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "published_date": result.get("published_date", "")
                })
            
            logger.info(f"Web search returned {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {e}")
            return []
    
    def search_company(self, company_name: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search for information about a specific company."""
        query = f"{company_name} company information recent news"
        return self.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )
    
    def search_industry_trends(self, industry: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for recent trends in a specific industry."""
        query = f"{industry} industry trends 2024 market analysis"
        return self.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )
    
    def search_job_market(self, role: str, location: str = "", max_results: int = 3) -> List[Dict[str, Any]]:
        """Search for job market information for a specific role."""
        query = f"{role} job market trends salary {location}".strip()
        return self.search(
            query=query,
            max_results=max_results,
            search_depth="basic"
        )


# Global instance
_web_search_tool = None


def get_web_search_tool() -> WebSearchTool:
    """Get the singleton web search tool instance."""
    global _web_search_tool
    if _web_search_tool is None:
        _web_search_tool = WebSearchTool()
    return _web_search_tool