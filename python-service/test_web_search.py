"""
Tests for the web search tool.
"""

import pytest
from unittest.mock import Mock, patch

from app.services.web_search import WebSearchTool, get_web_search_tool


class TestWebSearchTool:
    """Test the web search tool functionality."""
    
    def test_initialization_no_api_key(self):
        """Test initialization when API key is missing."""
        with patch('app.services.web_search.resolve_api_key', return_value=None):
            tool = WebSearchTool()
            assert not tool.is_available()
            assert tool.client is None
    
    def test_initialization_no_package(self):
        """Test initialization when Tavily package is missing."""
        with patch('app.services.web_search.TavilyClient', None):
            tool = WebSearchTool()
            assert not tool.is_available()
            assert tool.client is None
    
    @patch('app.services.web_search.resolve_api_key')
    @patch('app.services.web_search.TavilyClient')
    def test_successful_initialization(self, mock_tavily_client, mock_resolve_api_key):
        """Test successful initialization."""
        mock_resolve_api_key.return_value = "test-api-key"
        mock_client_instance = Mock()
        mock_tavily_client.return_value = mock_client_instance
        
        tool = WebSearchTool()
        
        assert tool.is_available()
        assert tool.client == mock_client_instance
        mock_tavily_client.assert_called_once_with(api_key="test-api-key")
    
    @patch('app.services.web_search.resolve_api_key')
    @patch('app.services.web_search.TavilyClient')
    def test_search_success(self, mock_tavily_client, mock_resolve_api_key):
        """Test successful search operation."""
        mock_resolve_api_key.return_value = "test-api-key"
        mock_client_instance = Mock()
        mock_tavily_client.return_value = mock_client_instance
        
        # Mock search response
        mock_response = {
            "results": [
                {
                    "title": "Test Result",
                    "url": "https://example.com",
                    "content": "Test content",
                    "score": 0.9,
                    "published_date": "2024-01-01"
                }
            ]
        }
        mock_client_instance.search.return_value = mock_response
        
        tool = WebSearchTool()
        results = tool.search("test query", max_results=5)
        
        assert len(results) == 1
        assert results[0]["title"] == "Test Result"
        assert results[0]["url"] == "https://example.com"
        assert results[0]["content"] == "Test content"
        assert results[0]["score"] == 0.9
        
        mock_client_instance.search.assert_called_once_with(
            query="test query",
            max_results=5,
            search_depth="basic"
        )
    
    def test_search_unavailable(self):
        """Test search when service is unavailable."""
        with patch('app.services.web_search.resolve_api_key', return_value=None):
            tool = WebSearchTool()
            results = tool.search("test query")
            assert results == []
    
    @patch('app.services.web_search.resolve_api_key')
    @patch('app.services.web_search.TavilyClient')
    def test_search_exception(self, mock_tavily_client, mock_resolve_api_key):
        """Test search with exception handling."""
        mock_resolve_api_key.return_value = "test-api-key"
        mock_client_instance = Mock()
        mock_tavily_client.return_value = mock_client_instance
        mock_client_instance.search.side_effect = Exception("API Error")
        
        tool = WebSearchTool()
        results = tool.search("test query")
        
        assert results == []
    
    @patch('app.services.web_search.resolve_api_key')
    @patch('app.services.web_search.TavilyClient')
    def test_search_company(self, mock_tavily_client, mock_resolve_api_key):
        """Test company search functionality."""
        mock_resolve_api_key.return_value = "test-api-key"
        mock_client_instance = Mock()
        mock_tavily_client.return_value = mock_client_instance
        mock_client_instance.search.return_value = {"results": []}
        
        tool = WebSearchTool()
        tool.search_company("OpenAI")
        
        mock_client_instance.search.assert_called_once()
        call_args = mock_client_instance.search.call_args
        assert "OpenAI company information recent news" in call_args.kwargs["query"]
        assert call_args.kwargs["max_results"] == 3
        assert call_args.kwargs["search_depth"] == "advanced"
    
    @patch('app.services.web_search.resolve_api_key')
    @patch('app.services.web_search.TavilyClient')
    def test_search_industry_trends(self, mock_tavily_client, mock_resolve_api_key):
        """Test industry trends search."""
        mock_resolve_api_key.return_value = "test-api-key"
        mock_client_instance = Mock()
        mock_tavily_client.return_value = mock_client_instance
        mock_client_instance.search.return_value = {"results": []}
        
        tool = WebSearchTool()
        tool.search_industry_trends("AI")
        
        mock_client_instance.search.assert_called_once()
        call_args = mock_client_instance.search.call_args
        assert "AI industry trends 2024 market analysis" in call_args.kwargs["query"]
        assert call_args.kwargs["max_results"] == 5
        assert call_args.kwargs["search_depth"] == "advanced"
    
    @patch('app.services.web_search.resolve_api_key')
    @patch('app.services.web_search.TavilyClient')
    def test_search_job_market(self, mock_tavily_client, mock_resolve_api_key):
        """Test job market search."""
        mock_resolve_api_key.return_value = "test-api-key"
        mock_client_instance = Mock()
        mock_tavily_client.return_value = mock_client_instance
        mock_client_instance.search.return_value = {"results": []}
        
        tool = WebSearchTool()
        tool.search_job_market("Software Engineer", "San Francisco")
        
        mock_client_instance.search.assert_called_once()
        call_args = mock_client_instance.search.call_args
        assert "Software Engineer job market trends salary San Francisco" in call_args.kwargs["query"]
        assert call_args.kwargs["max_results"] == 3
        assert call_args.kwargs["search_depth"] == "basic"
    
    def test_singleton_pattern(self):
        """Test that get_web_search_tool returns the same instance."""
        tool1 = get_web_search_tool()
        tool2 = get_web_search_tool()
        assert tool1 is tool2


if __name__ == "__main__":
    pytest.main([__file__])