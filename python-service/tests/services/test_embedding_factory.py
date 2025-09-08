"""Tests for embedding factory."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from dotenv import dotenv_values

from app.core.config import settings
from app.services.embeddings.factory import create_embedding_function, get_embedding_function


def test_create_sentence_transformer_embedding():
    """Test creating SentenceTransformer embedding function."""
    with patch('app.services.embeddings.factory.embedding_functions') as mock_ef:
        mock_st_func = MagicMock()
        mock_ef.SentenceTransformerEmbeddingFunction.return_value = mock_st_func
        
        result = create_embedding_function("sentence_transformer", "BAAI/bge-m3")
        
        mock_ef.SentenceTransformerEmbeddingFunction.assert_called_once_with(
            model_name="BAAI/bge-m3",
            normalize_embeddings=True,
            device="cpu"
        )
        assert result == mock_st_func


def test_create_openai_embedding():
    """Test creating OpenAI embedding function."""
    with patch('app.services.embeddings.factory.embedding_functions') as mock_ef, \
         patch('app.services.embeddings.factory.openai', True), \
         patch('app.services.embeddings.factory.resolve_api_key', return_value='test-key'):
        
        mock_openai_func = MagicMock()
        mock_ef.OpenAIEmbeddingFunction.return_value = mock_openai_func
        
        result = create_embedding_function("openai", "text-embedding-3-small")
        
        mock_ef.OpenAIEmbeddingFunction.assert_called_once_with(
            api_key='test-key',
            model_name="text-embedding-3-small"
        )
        assert result == mock_openai_func


def test_create_openai_embedding_no_package():
    """Test OpenAI embedding fails when package not installed."""
    with patch('app.services.embeddings.factory.openai', None):
        with pytest.raises(ValueError, match="OpenAI package not installed"):
            create_embedding_function("openai", "text-embedding-3-small")


def test_create_openai_embedding_no_api_key():
    """Test OpenAI embedding fails when API key not configured."""
    with patch('app.services.embeddings.factory.openai', True), \
         patch('app.services.embeddings.factory.resolve_api_key', return_value=None):
        
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            create_embedding_function("openai", "text-embedding-3-small")


def test_create_embedding_unsupported_provider():
    """Test unsupported provider raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported embedding provider: unsupported"):
        create_embedding_function("unsupported", "model")


def test_get_embedding_function():
    """Test getting embedding function from settings."""
    with patch('app.services.embeddings.factory.get_settings') as mock_settings, \
         patch('app.services.embeddings.factory.create_embedding_function') as mock_create:
        
        mock_settings.return_value.embedding_provider = "sentence_transformer"
        mock_settings.return_value.embedding_model = "BAAI/bge-m3"
        mock_func = MagicMock()
        mock_create.return_value = mock_func
        
        result = get_embedding_function()
        
        mock_create.assert_called_once_with("sentence_transformer", "BAAI/bge-m3")
        assert result == mock_func


def test_get_embedding_function_openai():
    """Test getting OpenAI embedding function from settings."""
    with patch('app.services.embeddings.factory.get_settings') as mock_settings, \
         patch('app.services.embeddings.factory.create_embedding_function') as mock_create:
        
        mock_settings.return_value.embedding_provider = "openai"
        mock_settings.return_value.embedding_model = "text-embedding-3-small"
        mock_func = MagicMock()
        mock_create.return_value = mock_func
        
        result = get_embedding_function()

        mock_create.assert_called_once_with("openai", "text-embedding-3-small")
        assert result == mock_func


def test_settings_reads_embedding_provider_from_env():
    """Settings should reflect EMBEDDING_PROVIDER from root .env."""
    env = dotenv_values(Path(__file__).resolve().parents[3] / ".env")
    assert settings.embedding_provider == env.get("EMBEDDING_PROVIDER")