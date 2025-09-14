"""Extensible ChromaDB manager for CrewAI integration."""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from loguru import logger
from enum import Enum

from .infrastructure import get_chroma_client
from .embeddings import get_embedding_function
from ..core.config import get_settings
from ..schemas.chroma import ChromaUploadRequest, ChromaUploadResponse, ChromaCollectionInfo


class CollectionType(Enum):
    """Enumeration of supported collection types for extensibility."""
    JOB_POSTINGS = "job_postings"
    COMPANY_PROFILES = "company_profiles"
    CAREER_BRANDS = "career_brands"
    INTERVIEW_FEEDBACK = "interview_feedback"
    MARKET_INSIGHTS = "market_insights"
    TECHNICAL_SKILLS = "technical_skills"
    GENERIC_DOCUMENTS = "documents"


class ChromaCollectionConfig:
    """Configuration for a ChromaDB collection."""
    
    def __init__(
        self,
        name: str,
        collection_type: CollectionType,
        description: str,
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        metadata_schema: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.collection_type = collection_type
        self.description = description
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.metadata_schema = metadata_schema or {}


class ChromaManager:
    """Extensible manager for ChromaDB operations across multiple collections."""
    
    def __init__(self):
        """Initialize the ChromaDB manager."""
        self.client = None
        self.embedding_function = None
        self.settings = get_settings()
        self._collection_configs: Dict[str, ChromaCollectionConfig] = {}
        self._initialize_default_collections()
    
    def _initialize_default_collections(self):
        """Initialize default collection configurations."""
        # Job postings collection for job analysis
        self.register_collection_config(ChromaCollectionConfig(
            name="job_postings",
            collection_type=CollectionType.JOB_POSTINGS,
            description="Job posting documents for analysis and matching",
            chunk_size=400,
            chunk_overlap=75,
            metadata_schema={
                "title": "str",
                "company": "str", 
                "location": "str",
                "salary_range": "str",
                "experience_level": "str",
                "skills": "list",
                "job_type": "str"
            }
        ))
        
        # Company profiles collection
        self.register_collection_config(ChromaCollectionConfig(
            name="company_profiles",
            collection_type=CollectionType.COMPANY_PROFILES,
            description="Company information and culture analysis",
            chunk_size=500,
            chunk_overlap=100,
            metadata_schema={
                "company_name": "str",
                "industry": "str",
                "size": "str",
                "culture_type": "str",
                "benefits": "list",
                "values": "list"
            }
        ))
        
        # Career brand documents for personal branding
        self.register_collection_config(ChromaCollectionConfig(
            name="career_brands",
            collection_type=CollectionType.CAREER_BRANDS,
            description="Personal career branding and positioning documents",
            chunk_size=300,
            chunk_overlap=50,
            metadata_schema={
                "profile_id": "str",
                "skill_category": "str",
                "experience_level": "str",
                "industry_focus": "str"
            }
        ))
        
        # Generic documents collection for future use
        self.register_collection_config(ChromaCollectionConfig(
            name="documents",
            collection_type=CollectionType.GENERIC_DOCUMENTS,
            description="Generic document storage for various purposes",
            chunk_size=300,
            chunk_overlap=50
        ))
    
    async def initialize(self):
        """Initialize the ChromaDB client and embedding function."""
        try:
            self.client = get_chroma_client()
            self.embedding_function = get_embedding_function()
            logger.info("ChromaDB manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB manager: {e}")
            raise
    
    def _get_client(self):
        """Get the ChromaDB client, initializing if needed."""
        if self.client is None:
            self.client = get_chroma_client()
        return self.client
    
    def _get_embedding_function(self):
        """Get the embedding function, initializing if needed."""
        if self.embedding_function is None:
            self.embedding_function = get_embedding_function()
        return self.embedding_function
    
    def register_collection_config(self, config: ChromaCollectionConfig):
        """Register a new collection configuration."""
        self._collection_configs[config.name] = config
        logger.info(f"Registered collection config: {config.name} ({config.collection_type.value})")
    
    def get_collection_config(self, collection_name: str) -> Optional[ChromaCollectionConfig]:
        """Get configuration for a collection."""
        return self._collection_configs.get(collection_name)
    
    def list_registered_collections(self) -> List[ChromaCollectionConfig]:
        """List all registered collection configurations."""
        return list(self._collection_configs.values())
    
    def _chunk_text(self, text: str, config: ChromaCollectionConfig) -> List[str]:
        """Split text into chunks based on collection configuration."""
        words = text.split()
        chunks = []
        start = 0
        
        while start < len(words):
            end = min(start + config.chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start = max(0, end - config.chunk_overlap)
        
        return chunks
    
    def _sha1_hash(self, text: str) -> str:
        """Generate SHA1 hash of text."""
        return hashlib.sha1(text.encode("utf-8")).hexdigest()
    
    async def ensure_collection_exists(self, collection_name: str) -> bool:
        """Ensure a collection exists, creating it if necessary."""
        try:
            client = self._get_client()
            embedding_function = self._get_embedding_function()
            config = self.get_collection_config(collection_name)
            
            expected_embed = f"{self.settings.embedding_provider}:{self.settings.embedding_model}"
            
            # Create collection with appropriate metadata
            collection_metadata = {
                "purpose": "crew_ai_rag",
                "embed_model": expected_embed,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            if config:
                collection_metadata.update({
                    "collection_type": config.collection_type.value,
                    "description": config.description,
                    "chunk_size": config.chunk_size,
                    "chunk_overlap": config.chunk_overlap
                })
            
            collection = client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_function,
                metadata=collection_metadata
            )
            
            logger.info(f"Collection '{collection_name}' is ready")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure collection '{collection_name}' exists: {e}")
            return False
    
    async def upload_document(
        self, 
        collection_name: str,
        title: str,
        document_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> ChromaUploadResponse:
        """Upload a document to a specific collection."""
        try:
            # Ensure collection exists
            if not await self.ensure_collection_exists(collection_name):
                return ChromaUploadResponse(
                    success=False,
                    message=f"Failed to ensure collection '{collection_name}' exists",
                    collection_name=collection_name,
                    document_id="",
                    chunks_created=0,
                    error_type="COLLECTION_ERROR"
                )
            
            client = self._get_client()
            config = self.get_collection_config(collection_name)
            
            # Get collection
            collection = client.get_collection(collection_name)
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Create chunks based on collection configuration
            if config:
                chunks = self._chunk_text(document_text, config)
            else:
                # Fallback to default chunking
                chunks = self._chunk_text(document_text, ChromaCollectionConfig(
                    name=collection_name,
                    collection_type=CollectionType.GENERIC_DOCUMENTS,
                    description="Generic collection"
                ))
            
            logger.info(f"Document '{title}' chunked into {len(chunks)} parts for collection '{collection_name}'")
            
            # Prepare data for ChromaDB
            ids = [f"{doc_id}::c{i}" for i in range(len(chunks))]
            tags_str = ", ".join(tags or [])
            created_at = datetime.now(timezone.utc).isoformat()
            
            metadatas = []
            for i, chunk in enumerate(chunks):
                base_metadata = {
                    "title": title,
                    "tags": tags_str,
                    "created_at": created_at,
                    "doc_id": doc_id,
                    "seq": i,
                    "content_hash": self._sha1_hash(chunk),
                    "type": "managed_document",
                    "collection_type": config.collection_type.value if config else "generic"
                }
                metadatas.append({**base_metadata, **(metadata or {})})
            
            # Add to collection
            collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas,
            )
            
            success_msg = f"Successfully uploaded document '{title}' with {len(chunks)} chunks to collection '{collection_name}'"
            logger.info(success_msg)
            
            return ChromaUploadResponse(
                success=True,
                message=success_msg,
                collection_name=collection_name,
                document_id=doc_id,
                chunks_created=len(chunks)
            )
            
        except Exception as e:
            error_msg = f"Failed to upload document to collection '{collection_name}': {str(e)}"
            logger.error(error_msg)
            return ChromaUploadResponse(
                success=False,
                message=error_msg,
                collection_name=collection_name,
                document_id="",
                chunks_created=0,
                error_type="UPLOAD_ERROR"
            )
    
    async def search_collection(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Search a specific collection for relevant documents."""
        try:
            client = self._get_client()
            
            # Ensure collection exists before searching
            if not await self.ensure_collection_exists(collection_name):
                return {
                    "success": False,
                    "error": f"Collection '{collection_name}' does not exist or could not be created",
                    "documents": [],
                    "metadatas": [],
                    "distances": []
                }
            
            collection = client.get_collection(collection_name)
            
            include_params = ["documents", "distances"]
            if include_metadata:
                include_params.append("metadatas")
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=include_params
            )
            
            return {
                "success": True,
                "collection_name": collection_name,
                "query": query,
                "documents": results.get("documents", [[]])[0],
                "metadatas": results.get("metadatas", [[]])[0] if include_metadata else [],
                "distances": results.get("distances", [[]])[0]
            }
            
        except Exception as e:
            logger.error(f"Failed to search collection '{collection_name}': {e}")
            return {
                "success": False,
                "error": str(e),
                "collection_name": collection_name,
                "query": query,
                "documents": [],
                "metadatas": [],
                "distances": []
            }
    
    async def search_across_collections(
        self,
        query: str,
        collection_names: Optional[List[str]] = None,
        n_results: int = 3,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Search across multiple collections."""
        try:
            client = self._get_client()
            
            # Determine which collections to search
            if collection_names is None:
                # Search all registered collections
                collection_names = list(self._collection_configs.keys())
            
            all_results = {}
            
            for collection_name in collection_names:
                result = await self.search_collection(
                    collection_name, query, n_results, include_metadata=include_metadata
                )
                all_results[collection_name] = result
            
            return {
                "success": True,
                "query": query,
                "collections_searched": collection_names,
                "results": all_results
            }
            
        except Exception as e:
            logger.error(f"Failed to search across collections: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": {}
            }
    
    async def get_collection_info(self, collection_name: str) -> Optional[ChromaCollectionInfo]:
        """Get information about a specific collection."""
        try:
            client = self._get_client()
            collection = client.get_collection(collection_name)
            count = collection.count()
            metadata = getattr(collection, 'metadata', {}) or {}
            
            return ChromaCollectionInfo(
                name=collection_name,
                count=count,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to get info for collection '{collection_name}': {e}")
            return None
    
    async def list_all_collections(self) -> List[ChromaCollectionInfo]:
        """List all existing ChromaDB collections."""
        try:
            client = self._get_client()
            collections = client.list_collections()
            
            result = []
            for collection in collections:
                info = await self.get_collection_info(collection.name)
                if info:
                    result.append(info)
                else:
                    # Add with minimal info if we can't get details
                    result.append(ChromaCollectionInfo(
                        name=collection.name,
                        count=0,
                        metadata={}
                    ))
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list ChromaDB collections: {e}")
            return []
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a ChromaDB collection."""
        try:
            client = self._get_client()
            client.delete_collection(collection_name)
            logger.info(f"Successfully deleted collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            return False


# Global manager instance
_chroma_manager: Optional[ChromaManager] = None


def get_chroma_manager() -> ChromaManager:
    """Get the global ChromaDB manager instance."""
    global _chroma_manager
    if _chroma_manager is None:
        _chroma_manager = ChromaManager()
    return _chroma_manager


async def ensure_default_collections():
    """Ensure all default collections exist."""
    manager = get_chroma_manager()
    await manager.initialize()
    
    for config in manager.list_registered_collections():
        await manager.ensure_collection_exists(config.name)
        logger.info(f"Ensured collection '{config.name}' exists")