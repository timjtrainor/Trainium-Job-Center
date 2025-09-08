"""Embedding services for ChromaDB integration."""

from .factory import create_embedding_function, get_embedding_function

__all__ = ["create_embedding_function", "get_embedding_function"]