"""ChromaDB client initialization."""

import chromadb
from typing import Union
import os
from loguru import logger

from ...core.config import get_settings


def get_chroma_client() -> Union[chromadb.HttpClient, chromadb.PersistentClient]:
    """Create and return a ChromaDB client using configured settings.
    
    Falls back to persistent client if HTTP client fails.
    """
    settings = get_settings()
    
    # First try HTTP client for production/docker environment
    try:
        client = chromadb.HttpClient(host=settings.chroma_url, port=settings.chroma_port)
        # Test the connection
        client.heartbeat()
        logger.info(f"Connected to ChromaDB HTTP server at {settings.chroma_url}:{settings.chroma_port}")
        return client
    except Exception as e:
        logger.warning(f"Could not connect to ChromaDB HTTP server: {e}")
        
        # Fall back to persistent client for development/local testing
        try:
            # Create a local data directory for ChromaDB
            persist_path = "./data/chroma"
            os.makedirs(persist_path, exist_ok=True)
            client = chromadb.PersistentClient(path=persist_path)
            logger.info(f"Using ChromaDB persistent client at {persist_path}")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB persistent client: {e}")
            raise RuntimeError(f"Could not initialize any ChromaDB client: {e}")
