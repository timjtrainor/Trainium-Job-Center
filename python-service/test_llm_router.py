"""
Tests for the LLM router and provider system.
"""

import pytest
from unittest.mock import Mock, patch
import os

from app.services.llm_clients import (
    LLMRouter, 
    OllamaClient, 
    OpenAIClient, 
    GeminiClient,
    create_llm_client
)


class TestLLMRouter:
    """Test the LLM routing system."""
    
    def test_router_initialization(self):
        """Test router initializes with correct providers."""
        preferences = "ollama:gemma3:1b,openai:gpt-4o-mini"
        router = LLMRouter(preferences)
        
        assert len(router.providers) == 2
        assert router.providers[0] == ("ollama", "gemma3:1b")
        assert router.providers[1] == ("openai", "gpt-4o-mini")
    
    def test_preference_parsing(self):
        """Test preference string parsing."""
        router = LLMRouter()
        
        # Test valid preferences
        providers = router._parse_preferences("ollama:gemma3:1b,openai:gpt-4")
        assert providers == [("ollama", "gemma3:1b"), ("openai", "gpt-4")]
        
        # Test with spaces
        providers = router._parse_preferences(" ollama : gemma3:1b , openai : gpt-4 ")
        assert providers == [("ollama", "gemma3:1b"), ("openai", "gpt-4")]
    
    @patch('app.services.llm_clients.create_llm_client')
    def test_client_creation(self, mock_create_client):
        """Test client creation and caching."""
        mock_client = Mock()
        mock_client.is_available.return_value = True
        mock_client.generate.return_value = "test response"
        mock_create_client.return_value = mock_client
        
        router = LLMRouter("ollama:gemma3:1b")
        
        # First call should create client
        client = router._get_client("ollama", "gemma3:1b")
        assert client == mock_client
        mock_create_client.assert_called_once_with("ollama", "gemma3:1b", host="http://localhost:11434")
        
        # Second call should use cached client
        mock_create_client.reset_mock()
        client2 = router._get_client("ollama", "gemma3:1b")
        assert client2 == mock_client
        mock_create_client.assert_not_called()
    
    @patch('app.services.llm_clients.create_llm_client')
    def test_generate_with_fallback(self, mock_create_client):
        """Test generation with provider fallback."""
        # First provider fails
        failing_client = Mock()
        failing_client.is_available.return_value = False
        
        # Second provider succeeds
        working_client = Mock()
        working_client.is_available.return_value = True
        working_client.generate.return_value = "success response"
        
        mock_create_client.side_effect = [failing_client, working_client]
        
        router = LLMRouter("ollama:gemma3:1b,openai:gpt-4")
        response = router.generate("test prompt")
        
        assert response == "success response"
        working_client.generate.assert_called_once_with("test prompt")
    
    @patch('app.services.llm_clients.create_llm_client')
    def test_all_providers_fail(self, mock_create_client):
        """Test error handling when all providers fail."""
        failing_client = Mock()
        failing_client.is_available.return_value = False
        mock_create_client.return_value = failing_client
        
        router = LLMRouter("ollama:gemma3:1b")
        
        with pytest.raises(ConnectionError, match="All LLM providers failed"):
            router.generate("test prompt")


class TestClientFactory:
    """Test the client factory function."""
    
    def test_create_ollama_client(self):
        """Test creating Ollama client."""
        client = create_llm_client("ollama", "gemma3:1b")
        assert isinstance(client, OllamaClient)
        assert client.model == "gemma3:1b"
        assert client.provider == "ollama"
    
    def test_create_openai_client(self):
        """Test creating OpenAI client."""
        client = create_llm_client("openai", "gpt-4")
        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-4"
        assert client.provider == "openai"
    
    def test_create_gemini_client(self):
        """Test creating Gemini client."""
        client = create_llm_client("gemini", "gemini-1.5-flash")
        assert isinstance(client, GeminiClient)
        assert client.model == "gemini-1.5-flash"
        assert client.provider == "gemini"
    
    def test_unsupported_provider(self):
        """Test error for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider: invalid"):
            create_llm_client("invalid", "model")


class TestClientAvailability:
    """Test client availability checking."""
    
    def test_ollama_availability_no_package(self):
        """Test Ollama availability when package not installed."""
        with patch('app.services.llm_clients.ollama', None):
            client = OllamaClient("gemma3:1b")
            assert not client.is_available()
    
    def test_openai_availability_no_api_key(self):
        """Test OpenAI availability when API key missing."""
        with patch('app.services.llm_clients.resolve_api_key', return_value=None):
            client = OpenAIClient("gpt-4")
            assert not client.is_available()
    
    def test_gemini_availability_no_api_key(self):
        """Test Gemini availability when API key missing."""
        with patch('app.services.llm_clients.resolve_api_key', return_value=None):
            client = GeminiClient("gemini-1.5-flash")
            assert not client.is_available()


if __name__ == "__main__":
    pytest.main([__file__])