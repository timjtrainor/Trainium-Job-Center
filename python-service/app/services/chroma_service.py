"""Service for ChromaDB operations."""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import List
from loguru import logger

from .infrastructure import get_chroma_client
from .embeddings import get_embedding_function
from ..core.config import get_settings
from ..schemas.chroma import ChromaUploadRequest, ChromaUploadResponse, ChromaCollectionInfo
from chromadb.errors import InvalidDimensionException, InvalidCollectionException


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
        try:
            client = self._get_client()
            embedding_function = self._get_embedding_function()
            expected_embed = f"{self.settings.embedding_provider}:{self.settings.embedding_model}"

            # Get or create collection
            collection = client.get_or_create_collection(
                name=request.collection_name,
                embedding_function=embedding_function,
                metadata={
                    "purpose": "user_uploaded_document",
                    "embed_model": expected_embed,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            )

            # Ensure embedding model matches configuration
            stored_embed = None
            if getattr(collection, "metadata", None):
                stored_embed = collection.metadata.get("embed_model")
            if stored_embed and stored_embed != expected_embed:
                raise ValueError(
                    "Embedding model mismatch: collection uses "
                    f"'{stored_embed}' but settings specify '{expected_embed}'. "
                    "Delete or recreate the collection."
                )
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Create chunks
            chunks = self._chunk_text(request.document_text)
            
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
                collection.add(
                    ids=ids,
                    documents=chunks,
                    metadatas=metadatas
                )
            except (InvalidDimensionException, InvalidCollectionException, Exception) as e:
                server_message = getattr(e, "message", None) or (e.args[0] if e.args else str(e))
                raise ValueError(server_message) from e
            
            logger.info(
                f"Successfully uploaded document to collection '{request.collection_name}' "
                f"with {len(chunks)} chunks"
            )
            
            return ChromaUploadResponse(
                success=True,
                message=f"Successfully uploaded document with {len(chunks)} chunks",
                collection_name=request.collection_name,
                document_id=doc_id,
                chunks_created=len(chunks)
            )
            
        except Exception as e:
            logger.error(f"Failed to upload document to ChromaDB: {e}")
            return ChromaUploadResponse(
                success=False,
                message=f"Upload failed: {str(e)}",
                collection_name=request.collection_name,
                document_id="",
                chunks_created=0
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
