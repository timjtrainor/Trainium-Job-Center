"""Service for ChromaDB operations."""

import uuid
import hashlib
import traceback
from datetime import datetime, timezone
from typing import List
from loguru import logger

from .infrastructure import get_chroma_client
from .embeddings import get_embedding_function
from ..core.config import get_settings
from ..schemas.chroma import ChromaUploadRequest, ChromaUploadResponse, ChromaCollectionInfo
from chromadb.errors import (
    ChromaError,
    InvalidDimensionException,
    InvalidCollectionException,
)


class ChromaService:
    """Service for managing ChromaDB operations."""
    
    def __init__(self):
        """Initialize the ChromaDB service."""
        self.client = None
        self.embedding_function = None
        self.settings = get_settings()
    
    async def initialize(self):
        """Initialize the ChromaDB client and embedding function."""
        try:
            self.client = get_chroma_client()
            self.embedding_function = get_embedding_function()
            logger.info("ChromaDB service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB service: {e}")
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
    
    def _chunk_text(self, text: str, words_per_chunk: int = 300, overlap: int = 50) -> List[str]:
        """Split text into chunks for better vector storage."""
        words = text.split()
        chunks = []
        start = 0
        
        while start < len(words):
            end = min(start + words_per_chunk, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start = max(0, end - overlap)
        
        return chunks
    
    def _sha1_hash(self, text: str) -> str:
        """Generate SHA1 hash of text."""
        return hashlib.sha1(text.encode("utf-8")).hexdigest()
    
    async def upload_document(self, request: ChromaUploadRequest) -> ChromaUploadResponse:
        """Upload a document to ChromaDB."""
        logger.info(
            f"Starting upload to collection '{request.collection_name}' "
            f"with title '{request.title}' and {len(request.document_text)} chars"
        )
        
        try:
            client = self._get_client()
            embedding_function = self._get_embedding_function()
            expected_embed = f"{self.settings.embedding_provider}:{self.settings.embedding_model}"
            
            logger.info(f"Using embedding configuration: {expected_embed}")

            # Get or create collection
            try:
                collection = client.get_or_create_collection(
                    name=request.collection_name,
                    embedding_function=embedding_function,
                    metadata={
                        "purpose": "user_uploaded_document",
                        "embed_model": expected_embed,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                logger.info(f"Successfully accessed collection '{request.collection_name}'")
            except Exception as e:
                logger.error(f"Failed to get/create collection '{request.collection_name}': {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return ChromaUploadResponse(
                    success=False,
                    message=f"Failed to access collection '{request.collection_name}': {str(e)}. "
                           f"This may be due to ChromaDB connection issues or embedding configuration problems.",
                    collection_name=request.collection_name,
                    document_id="",
                    chunks_created=0,
                    error_type="CONNECTION_ERROR",
                    suggestions=[
                        "Check if ChromaDB service is running",
                        "Verify CHROMA_URL and CHROMA_PORT in your .env file",
                        "Check embedding provider configuration"
                    ]
                )

            # Ensure embedding model matches configuration
            metadata = getattr(collection, "metadata", {}) or {}
            stored_embed = metadata.get("embed_model")
            
            if stored_embed and stored_embed != expected_embed:
                error_msg = (
                    f"Embedding model mismatch detected!\n"
                    f"Collection '{request.collection_name}' was created with: {stored_embed}\n"
                    f"Current configuration expects: {expected_embed}\n\n"
                    f"This happens when you change embedding providers or models after creating collections.\n"
                    f"Solutions:\n"
                    f"1. Delete the collection and recreate it: DELETE /chroma/collections/{request.collection_name}\n"
                    f"2. Or change your .env back to: EMBEDDING_PROVIDER={stored_embed.split(':')[0]}, "
                    f"EMBEDDING_MODEL={stored_embed.split(':', 1)[1] if ':' in stored_embed else stored_embed}\n"
                    f"3. Or use a different collection name for the new embedding model"
                )
                logger.error(f"Embedding model mismatch: {error_msg}")
                return ChromaUploadResponse(
                    success=False,
                    message=error_msg,
                    collection_name=request.collection_name,
                    document_id="",
                    chunks_created=0,
                    error_type="EMBEDDING_MISMATCH",
                    suggestions=[
                        f"Delete collection: DELETE /chroma/collections/{request.collection_name}",
                        "Use a different collection name",
                        f"Revert .env to previous embedding settings"
                    ]
                )
            
            logger.info(f"Embedding model validation passed for collection '{request.collection_name}'")
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Create chunks
            chunks = self._chunk_text(request.document_text)
            logger.info(f"Document chunked into {len(chunks)} parts")
            
            # Prepare data for ChromaDB
            ids = [f"{doc_id}::c{i}" for i in range(len(chunks))]
            tags_str = ", ".join(request.tags)
            metadatas = [{
                "title": request.title,
                "tags": tags_str,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "doc_id": doc_id,
                "seq": i,
                "content_hash": self._sha1_hash(chunks[i]),
                "type": "user_document"
            } for i in range(len(chunks))]
            
            # Add to collection with explicit error handling
            try:
                logger.info(f"Adding {len(chunks)} chunks to ChromaDB collection '{request.collection_name}'")
                collection.add(
                    ids=ids,
                    documents=chunks,
                    metadatas=metadatas,
                )
                logger.info(f"Successfully added all chunks to collection '{request.collection_name}'")
            except (InvalidDimensionException, InvalidCollectionException, ChromaError) as e:
                error_msg = (
                    f"ChromaDB operation failed: {str(e)}\n"
                    f"Error type: {type(e).__name__}\n"
                    f"Collection: {request.collection_name}\n"
                    f"Embedding model: {expected_embed}\n\n"
                    f"This error often occurs when:\n"
                    f"1. Embedding model configuration has changed\n"
                    f"2. ChromaDB service is not properly configured\n"
                    f"3. Collection was created with different embedding settings\n\n"
                    f"Try recreating the collection or checking your embedding configuration."
                )
                logger.error(f"ChromaDB add failed: {error_msg}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return ChromaUploadResponse(
                    success=False,
                    message=error_msg,
                    collection_name=request.collection_name,
                    document_id="",
                    chunks_created=0,
                    error_type="CHROMADB_ERROR",
                    suggestions=[
                        "Try recreating the collection",
                        "Check embedding configuration in .env",
                        "Verify ChromaDB service is running properly",
                        "Check the application logs for more details"
                    ]
                )
            except Exception as e:
                error_msg = (
                    f"Unexpected error during ChromaDB upload: {str(e)}\n"
                    f"Error type: {type(e).__name__}\n"
                    f"Collection: {request.collection_name}\n"
                    f"Document chunks: {len(chunks)}\n\n"
                    f"This may indicate a system or configuration issue. "
                    f"Check the logs for more details."
                )
                logger.error(f"Unexpected ChromaDB error: {error_msg}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return ChromaUploadResponse(
                    success=False,
                    message=error_msg,
                    collection_name=request.collection_name,
                    document_id="",
                    chunks_created=0,
                    error_type="UNEXPECTED_ERROR",
                    suggestions=[
                        "Check the application logs for more details",
                        "Restart the ChromaDB service",
                        "Verify system resources and configuration"
                    ]
                )
            
            success_msg = f"Successfully uploaded document '{request.title}' with {len(chunks)} chunks to collection '{request.collection_name}'"
            logger.info(success_msg)
            
            return ChromaUploadResponse(
                success=True,
                message=success_msg,
                collection_name=request.collection_name,
                document_id=doc_id,
                chunks_created=len(chunks)
            )
            
        except Exception as e:
            error_msg = (
                f"Failed to upload document to ChromaDB: {str(e)}\n"
                f"Error type: {type(e).__name__}\n"
                f"Collection: {request.collection_name}\n"
                f"Title: {request.title}\n\n"
                f"This is an unexpected system error. Check the application logs for more details."
            )
            logger.error(f"Upload document failed: {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return ChromaUploadResponse(
                success=False,
                message=error_msg,
                collection_name=request.collection_name,
                document_id="",
                chunks_created=0,
                error_type="SYSTEM_ERROR",
                suggestions=[
                    "Check the application logs for more details",
                    "Verify ChromaDB service connectivity",
                    "Check embedding provider configuration",
                    "Contact system administrator if the issue persists"
                ]
            )
    
    async def list_collections(self) -> List[ChromaCollectionInfo]:
        """List all ChromaDB collections."""
        try:
            client = self._get_client()
            collections = client.list_collections()
            
            result = []
            for collection in collections:
                try:
                    # Get collection info
                    coll = client.get_collection(collection.name)
                    count = coll.count()
                    metadata = collection.metadata
                    
                    result.append(ChromaCollectionInfo(
                        name=collection.name,
                        count=count,
                        metadata=metadata
                    ))
                except Exception as e:
                    logger.warning(f"Failed to get info for collection {collection.name}: {e}")
                    # Add with minimal info
                    result.append(ChromaCollectionInfo(
                        name=collection.name,
                        count=0,
                        metadata=None
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
