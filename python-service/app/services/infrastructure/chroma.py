"""ChromaDB client initialization."""

from typing import Union
import chromadb

from ...core.config import get_settings


def get_chroma_client() -> Union[chromadb.HttpClient, chromadb.PersistentClient]:
    """Create and return a ChromaDB client using configured settings."""
    settings = get_settings()
    return settings.create_chroma_client()
