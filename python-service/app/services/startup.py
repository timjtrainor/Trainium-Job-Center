"""Application startup services and initialization."""

import asyncio
from loguru import logger

from .chroma_integration_service import get_chroma_integration_service
from .chroma_manager import ensure_default_collections


async def initialize_chroma_collections():
    """Initialize ChromaDB collections on application startup."""
    try:
        logger.info("Initializing ChromaDB collections...")
        
        # Initialize the integration service
        service = get_chroma_integration_service()
        await service.initialize()
        
        # Ensure default collections exist
        await ensure_default_collections()
        
        logger.info("ChromaDB collections initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB collections: {e}")
        logger.warning("Application will continue but ChromaDB functionality may be limited")


async def startup_tasks():
    """Run all startup tasks."""
    logger.info("Running application startup tasks...")
    
    # Initialize ChromaDB (non-blocking)
    try:
        await initialize_chroma_collections()
    except Exception as e:
        logger.error(f"ChromaDB initialization failed: {e}")
    
    logger.info("Application startup tasks completed")