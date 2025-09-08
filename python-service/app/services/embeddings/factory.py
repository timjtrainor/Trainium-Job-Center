"""Factory for creating embedding functions for ChromaDB."""

from typing import Union
from loguru import logger
from chromadb.utils import embedding_functions

try:
    import openai
except ImportError:
    openai = None

from ...core.config import get_settings, resolve_api_key


def create_embedding_function(
    provider: str, model: str
) -> Union[
    embedding_functions.SentenceTransformerEmbeddingFunction,
    embedding_functions.OpenAIEmbeddingFunction
]:
    """Create an embedding function based on provider and model.
    
    Args:
        provider: Embedding provider ('sentence_transformer' or 'openai')
        model: Model name for the provider
        
    Returns:
        ChromaDB embedding function
        
    Raises:
        ValueError: If provider is unsupported or configuration is missing
    """
    provider = provider.lower()
    
    if provider == "sentence_transformer":
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model,
            normalize_embeddings=True,
            device="cpu"  # Use CPU for compatibility
        )
    elif provider == "openai":
        if openai is None:
            raise ValueError("OpenAI package not installed")
        
        api_key = resolve_api_key("openai")
        if not api_key:
            raise ValueError("OpenAI API key not configured")
            
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name=model
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


def get_embedding_function() -> Union[
    embedding_functions.SentenceTransformerEmbeddingFunction,
    embedding_functions.OpenAIEmbeddingFunction
]:
    """Get the configured embedding function from settings.
    
    Returns:
        ChromaDB embedding function based on configuration
    """
    settings = get_settings()
    provider = settings.embedding_provider
    model = settings.embedding_model
    
    logger.info(f"Creating embedding function: {provider}:{model}")
    return create_embedding_function(provider, model)