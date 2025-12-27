"""Factory for creating embedding functions for ChromaDB."""

from typing import Union
from loguru import logger
from chromadb.utils import embedding_functions

try:
    import openai
except ImportError:
    openai = None

from ...core.config import get_settings, resolve_api_key


# Global cache for embedding functions to avoid reloading models on every request
_embedding_function_cache = {}

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
    cache_key = f"{provider}:{model}"
    
    if cache_key in _embedding_function_cache:
        logger.debug(f"Using cached embedding function for {cache_key}")
        return _embedding_function_cache[cache_key]
    
    logger.info(f"Creating new embedding function for {cache_key}")
    
    if provider == "sentence_transformer":
        try:
            func = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model,
                normalize_embeddings=True,
                device="cpu"  # Use CPU for compatibility
            )
            _embedding_function_cache[cache_key] = func
            return func
        except Exception as e:
            raise ValueError(
                f"Failed to create SentenceTransformer embedding function with model '{model}'. "
                f"Error: {str(e)}. Make sure the model name is valid and accessible."
            ) from e
            
    elif provider == "openai":
        if openai is None:
            raise ValueError(
                "OpenAI package not installed. Run: pip install openai"
            )
        
        api_key = resolve_api_key("openai")
        if not api_key:
            raise ValueError(
                "OpenAI API key not configured. Set OPENAI_API_KEY in your .env file."
            )
            
        try:
            func = embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name=model
            )
            _embedding_function_cache[cache_key] = func
            return func
        except Exception as e:
            raise ValueError(
                f"Failed to create OpenAI embedding function with model '{model}'. "
                f"Error: {str(e)}. Check your API key and model name."
            ) from e
    else:
        supported_providers = ["sentence_transformer", "openai"]
        raise ValueError(
            f"Unsupported embedding provider: '{provider}'. "
            f"Supported providers are: {', '.join(supported_providers)}"
        )


def get_embedding_function() -> Union[
    embedding_functions.SentenceTransformerEmbeddingFunction,
    embedding_functions.OpenAIEmbeddingFunction
]:
    """Get the configured embedding function from settings.
    
    Returns:
        ChromaDB embedding function based on configuration
        
    Raises:
        ValueError: If configuration is invalid or missing
    """
    settings = get_settings()
    provider = settings.embedding_provider
    model = settings.embedding_model
    
    try:
        return create_embedding_function(provider, model)
    except Exception as e:
        error_msg = (
            f"Failed to create embedding function with {provider}:{model}. "
            f"Error: {str(e)}. "
            f"Check your .env configuration for EMBEDDING_PROVIDER and EMBEDDING_MODEL."
        )
        logger.error(error_msg)
        raise ValueError(error_msg) from e