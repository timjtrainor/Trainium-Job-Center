"""ChromaDB client initialization."""

import chromadb

from ...core.config import get_settings


def get_chroma_client() -> chromadb.HttpClient:
    """Create and return a ChromaDB HTTP client using configured settings."""
    settings = get_settings()
    return chromadb.HttpClient(host=settings.chroma_url, port=settings.chroma_port)
