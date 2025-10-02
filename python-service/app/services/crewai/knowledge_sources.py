"""
Custom Knowledge Sources for CrewAI integration with ChromaDB.

This module provides concrete implementations of CrewAI knowledge sources
that work with the ChromaDB vector database for agent context and memory.
"""

from typing import Any, Dict, List, Optional
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource
from loguru import logger

from ..chroma_service import ChromaService


class ChromaKnowledgeSource(BaseKnowledgeSource):
    """
    CrewAI knowledge source that integrates with ChromaDB.

    Provides vector-based retrieval of relevant documents for agent context.
    """

    collection_name: str
    host: str = "chromadb"
    port: int = 8001
    filters: Optional[Dict[str, Any]] = {}
    top_k: int = 5

    def __init__(
        self,
        collection_name: str,
        host: str = "chromadb",
        port: int = 8001,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        search_type: str = "similarity"
    ):
        """
        Initialize ChromaDB knowledge source.

        Args:
            collection_name: Name of ChromaDB collection to query
            host: ChromaDB server hostname
            port: ChromaDB server port
            filters: Metadata filters for document retrieval
            top_k: Maximum number of documents to retrieve
            search_type: Type of search ("similarity" or "mmr")
        """
        # Initialize Pydantic model with required data
        data = {
            'collection_name': collection_name,
            'host': host,
            'port': port,
            'filters': filters or {},
            'top_k': top_k
        }
        super().__init__(**data)
        # Store non-pydantic attributes
        object.__setattr__(self, '_search_type', search_type)

        # Initialize ChromaDB client
        self._chroma_service = ChromaService()
        logger.info(f"Initialized ChromaKnowledgeSource for collection: {collection_name}")

    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add content to the knowledge source.

        Args:
            content: Text content to add
            metadata: Optional metadata for the content
        """
        try:
            # Use ChromaDB service to add document
            metadata = metadata or {}
            document_id = f"{self.collection_name}_{hash(content)}"

            # Add required metadata for filtering
            metadata.update({
                "collection": self.collection_name,
                "source": "crewai_knowledge_source"
            })

            self._chroma_service.add_documents(
                collection_name=self.collection_name,
                documents=[content],
                metadatas=[metadata],
                ids=[document_id]
            )

            logger.info(f"Added content to ChromaDB collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to add content to ChromaDB: {e}")
            raise

    def validate_content(self, content: Any) -> bool:
        """
        Validate that content can be added to this knowledge source.

        Args:
            content: Content to validate

        Returns:
            True if content is valid for this knowledge source
        """
        if not isinstance(content, str):
            logger.warning(f"Content must be string, got {type(content)}")
            return False

        if len(content.strip()) == 0:
            logger.warning("Content cannot be empty")
            return False

        # Content is valid if it can be processed
        return True

    def query(self, query: str, filters: Optional[Dict[str, Any]] = None, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query the knowledge source for relevant documents.

        Args:
            query: Search query
            filters: Additional metadata filters
            top_k: Number of results to return

        Returns:
            List of relevant documents with metadata
        """
        try:
            # Combine base filters with query-specific filters
            query_filters = self.filters.copy()
            if filters:
                query_filters.update(filters)

            # Set default collection in filters if not present
            if "collection" not in query_filters:
                query_filters["collection"] = self.collection_name

            # Perform similarity search
            results = self._chroma_service.similarity_search(
                collection_name=self.collection_name,
                query=query,
                k=top_k or self.top_k,
                filters=query_filters
            )

            logger.info(f"Queried ChromaDB for '{query}': found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}")
            return []

    def search(self, query: str, **kwargs) -> List[str]:
        """
        Search the knowledge source (required by CrewAI BaseKnowledgeSource).

        Args:
            query: Search query
            **kwargs: Additional search parameters

        Returns:
            List of relevant text content
        """
        results = self.query(query, **kwargs)
        return [result.get('content', '') for result in results if result.get('content')]


def create_knowledge_source_from_config(config: Dict[str, Any]) -> ChromaKnowledgeSource:
    """
    Create a ChromaKnowledgeSource from a configuration dictionary.

    Args:
        config: Configuration dictionary with ChromaDB connection details

    Returns:
        Configured ChromaKnowledgeSource instance
    """
    if config.get("type") != "chroma":
        raise ValueError(f"Unsupported knowledge source type: {config.get('type')}")

    chroma_config = config.get("config", {})
    return ChromaKnowledgeSource(
        collection_name=chroma_config.get("collection"),
        host=chroma_config.get("host", "chromadb"),
        port=chroma_config.get("port", 8001),
        filters=chroma_config.get("filters", {}),
        top_k=chroma_config.get("top_k", 5)
    )


# Factory function for agent configuration
def get_knowledge_sources_from_config(sources_config: List[Dict[str, Any]]) -> List[ChromaKnowledgeSource]:
    """
    Convert knowledge source configurations to concrete ChromaKnowledgeSource instances.

    This function is called by CrewAI when parsing agent configurations.
    """
    knowledge_sources = []

    for source_config in sources_config:
        try:
            if source_config.get("type") == "chroma":
                ks = create_knowledge_source_from_config(source_config)
                knowledge_sources.append(ks)
                logger.info(f"Created Chroma knowledge source for collection: {source_config.get('config', {}).get('collection')}")
        except Exception as e:
            logger.error(f"Failed to create knowledge source: {e}")

    return knowledge_sources
