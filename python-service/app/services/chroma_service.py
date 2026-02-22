"""Service for ChromaDB operations."""

import json
import uuid
import hashlib
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Any
from loguru import logger

from .infrastructure import get_chroma_client
from .embeddings import get_embedding_function
from ..core.config import get_settings
from ..schemas.chroma import ChromaUploadRequest, ChromaUploadResponse, ChromaCollectionInfo
from chromadb.errors import (
    ChromaError,
    InvalidDimensionException,
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

    def _parse_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to parse JSON-encoded metadata values."""
        parsed: Dict[str, Any] = {}
        for key, value in (metadata or {}).items():
            if isinstance(value, str):
                stripped = value.strip()
                if (stripped.startswith("{") and stripped.endswith("}")) or (
                    stripped.startswith("[") and stripped.endswith("]")
                ):
                    try:
                        parsed[key] = json.loads(stripped)
                        continue
                    except json.JSONDecodeError:
                        pass
            parsed[key] = value
        return parsed

    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Convert simple equality filters into Chroma's where format."""
        clauses = []
        for key, value in (filters or {}).items():
            if value is None:
                continue
            clauses.append({key: {"$eq": value}})

        if not clauses:
            return {}
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}
    
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
            created_at = datetime.now(timezone.utc).isoformat()
            metadatas = []
            for i, chunk in enumerate(chunks):
                base_metadata = {
                    "title": request.title,
                    "tags": tags_str,
                    "created_at": created_at,
                    "doc_id": doc_id,
                    "seq": i,
                    "content_hash": self._sha1_hash(chunk),
                    "type": "user_document",
                }
                metadatas.append({**base_metadata, **request.metadata})
            
            # Add to collection with explicit error handling
            try:
                logger.info(f"Adding {len(chunks)} chunks to ChromaDB collection '{request.collection_name}'")
                collection.add(
                    ids=ids,
                    documents=chunks,
                    metadatas=metadatas,
                )
                logger.info(f"Successfully added all chunks to collection '{request.collection_name}'")
            except (InvalidDimensionException, ChromaError) as e:
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
    
    async def list_documents(self, collection_name: str) -> List[dict]:
        """List all documents in a ChromaDB collection."""
        try:
            client = self._get_client()
            collection = client.get_collection(collection_name)

            result = collection.get(include=["metadatas", "documents"])

            grouped_docs: Dict[str, dict] = {}

            ids = result.get("ids", []) or []
            metadatas = result.get("metadatas", []) or []
            documents = result.get("documents", []) or []
            
            logger.info(f"Retrieved {len(ids)} chunks from collection '{collection_name}' for listing")

            for idx, chunk_id in enumerate(ids):
                metadata = metadatas[idx] if idx < len(metadatas) else {}
                document_text = documents[idx] if idx < len(documents) else ""

                document_id = metadata.get(
                    "doc_id",
                    chunk_id.split("::")[0] if "::" in chunk_id else chunk_id
                )

                entry = grouped_docs.setdefault(
                    document_id,
                    {
                        "id": document_id,
                        "title": metadata.get("title", "Untitled"),
                        "created_at": metadata.get("created_at")
                        or metadata.get("uploaded_at")
                        or datetime.now(timezone.utc).isoformat(),
                        "chunk_count": 0,
                        "type": metadata.get("type", "document"),
                        "collection_name": collection_name,
                        "metadata": metadata,
                        "_snippet_seq": metadata.get("seq", 0),
                        "content_snippet": document_text,
                    },
                )

                entry["chunk_count"] += 1

                # Prefer metadata from the most recent chunk
                entry_uploaded = entry["metadata"].get("uploaded_at") if entry.get("metadata") else None
                current_uploaded = metadata.get("uploaded_at")
                if current_uploaded and (not entry_uploaded or current_uploaded > entry_uploaded):
                    entry["metadata"] = metadata

                # Store snippet from lowest sequence chunk
                current_seq = metadata.get("seq", 0)
                if current_seq < entry.get("_snippet_seq", current_seq + 1):
                    entry["_snippet_seq"] = current_seq
                    entry["content_snippet"] = document_text

                if not entry.get("title") and metadata.get("title"):
                    entry["title"] = metadata.get("title")

            documents_list: List[dict] = []
            for doc in grouped_docs.values():
                metadata = self._parse_metadata(doc.get("metadata", {}))
                documents_list.append(
                    {
                        "id": doc["id"],
                        "title": doc.get("title", "Untitled"),
                        "collection_name": doc["collection_name"],
                        "created_at": doc.get("created_at"),
                        "chunk_count": doc.get("chunk_count", 0),
                        "section": metadata.get("section", ""),
                        "content_snippet": (doc.get("content_snippet") or "")[:500],
                        "metadata": metadata,
                    }
                )

            logger.info(f"Grouped collection '{collection_name}' into {len(documents_list)} unique documents")
            return documents_list

        except Exception as e:
            logger.error(f"Failed to list documents in collection '{collection_name}': {e}")
            return []
    
    async def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Delete a specific document from a ChromaDB collection."""
        try:
            client = self._get_client()
            collection = client.get_collection(collection_name)
            
            # Efficiently get only the relevant chunk IDs using where filter
            where_clause = self._build_where_clause({"doc_id": document_id})
            result = collection.get(where=where_clause, include=["metadatas"])
            chunk_ids_to_delete = result.get("ids", [])
            
            # Fallback for legacy documents without doc_id in metadata
            if not chunk_ids_to_delete:
                logger.info(f"Document '{document_id}' not found with doc_id filter in '{collection_name}', scanning collection...")
                result = collection.get(include=["metadatas"])
                for i, chunk_id in enumerate(result.get("ids", [])):
                    metadata = result["metadatas"][i] if result.get("metadatas") else {}
                    doc_id = metadata.get("doc_id", chunk_id.split("::")[0] if "::" in chunk_id else chunk_id)
                    
                    if doc_id == document_id:
                        chunk_ids_to_delete.append(chunk_id)
            
            if chunk_ids_to_delete:
                collection.delete(ids=chunk_ids_to_delete)
                logger.info(f"Successfully deleted document '{document_id}' ({len(chunk_ids_to_delete)} chunks) from collection '{collection_name}'")
                return True
            else:
                logger.warning(f"Document '{document_id}' not found in collection '{collection_name}'")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document '{document_id}' from collection '{collection_name}': {e}")
            return False

    def _deduplicate_chunks(self, chunks: List[str]) -> str:
        """
        Merge overlapping chunks to reconstruct the original text.
        Assumes chunks are in correct sequence and may overlap.
        """
        if not chunks:
            return ""
        if len(chunks) == 1:
            return chunks[0]

        merged_text = chunks[0]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # Find overlap
            # We look for the longest suffix of prev_chunk that matches a prefix of current_chunk
            # We restrict search to a reasonable window (e.g., last 200 chars) to valid false positives
            
            overlap_len = 0
            # Default overlap in _chunk_text is usually small (e.g. 50 words), so 1000 chars is safe upper bound
            search_window_size = min(len(prev_chunk), 2000) 
            search_window = prev_chunk[-search_window_size:]
            
            # Try to find the overlap
            for j in range(len(search_window)):
                suffix = search_window[j:]
                if current_chunk.startswith(suffix):
                    overlap_len = len(suffix)
                    break
            
            if overlap_len > 0:
                merged_text += current_chunk[overlap_len:]
            else:
                # No overlap found, just append (should ideally not happen if chunking is consistent)
                merged_text += current_chunk

        return merged_text

    async def get_document_detail(self, collection_name: str, document_id: str) -> Dict[str, Any]:
        """Retrieve full document content and metadata for a specific document."""
        client = self._get_client()
        collection = client.get_collection(collection_name)

        where_clause = self._build_where_clause({"doc_id": document_id})
        result = collection.get(where=where_clause, include=["metadatas", "documents"])

        ids = result.get("ids", []) or []
        metadatas = result.get("metadatas", []) or []
        documents = result.get("documents", []) or []

        if not ids:
            # fall back to scanning entire collection for legacy records
            fallback = collection.get(include=["metadatas", "documents"])
            ids = fallback.get("ids", []) or []
            metadatas = fallback.get("metadatas", []) or []
            documents = fallback.get("documents", []) or []

        chunks: List[tuple[int, str]] = []
        aggregated_metadata: Dict[str, Any] = {}

        for idx, chunk_id in enumerate(ids):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            doc_id = metadata.get(
                "doc_id",
                chunk_id.split("::")[0] if "::" in chunk_id else chunk_id
            )

            if doc_id != document_id:
                continue

            document_text = documents[idx] if idx < len(documents) else ""
            seq = metadata.get("seq", idx)
            chunks.append((seq, document_text))

            uploaded_at = aggregated_metadata.get("uploaded_at")
            current_uploaded = metadata.get("uploaded_at")
            if current_uploaded and (not uploaded_at or current_uploaded > uploaded_at):
                aggregated_metadata = metadata
            elif not aggregated_metadata:
                aggregated_metadata = metadata

        if not chunks and not aggregated_metadata:
            raise ValueError(f"Document '{document_id}' not found in collection '{collection_name}'")

        chunks.sort(key=lambda item: item[0])
        # Use deduplication logic instead of simple join
        content = self._deduplicate_chunks([chunk for _, chunk in chunks])

        parsed_metadata = self._parse_metadata(aggregated_metadata)

        return {
            "id": document_id,
            "title": parsed_metadata.get("title", "Untitled"),
            "collection_name": collection_name,
            "metadata": parsed_metadata,
            "content": content,
            "chunk_count": len(chunks),
            "created_at": parsed_metadata.get("created_at")
            or parsed_metadata.get("uploaded_at"),
        }

    async def update_document_metadata(self, collection_name: str, document_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """Update metadata for all chunks of a specific document."""
        try:
            client = self._get_client()
            collection = client.get_collection(collection_name)

            # First try with doc_id filter
            where_clause = self._build_where_clause({"doc_id": document_id})
            result = collection.get(where=where_clause, include=["metadatas"])

            if not result["ids"] or not result["metadatas"]:
                # Fallback: scan entire collection for legacy documents
                logger.info(f"Document '{document_id}' not found with doc_id filter, trying legacy scan")
                fallback_result = collection.get(include=["metadatas", "ids"])

                chunk_ids_to_update = []
                current_metadatas = []

                for i, chunk_id in enumerate(fallback_result["ids"]):
                    metadata = fallback_result["metadatas"][i] if fallback_result["metadatas"] else {}
                    doc_id = metadata.get("doc_id", chunk_id.split("::")[0] if "::" in chunk_id else chunk_id)

                    if doc_id == document_id:
                        chunk_ids_to_update.append(chunk_id)
                        current_metadatas.append(metadata)

                if not chunk_ids_to_update:
                    logger.warning(f"Document '{document_id}' not found in collection '{collection_name}' even with legacy scan")
                    return False

                result = {"ids": chunk_ids_to_update, "metadatas": current_metadatas}

            chunk_ids_to_update = result["ids"]
            current_metadatas = result["metadatas"]

            # Update each chunk's metadata
            updated_metadatas = []
            for metadata in current_metadatas:
                if metadata is None:
                    metadata = {}
                # Create a copy and update with new metadata
                updated_metadata = dict(metadata)
                updated_metadata.update(metadata_updates)
                updated_metadatas.append(updated_metadata)

            # Update the metadata for all chunks
            collection.update(ids=chunk_ids_to_update, metadatas=updated_metadatas)

            logger.info(f"Successfully updated metadata for document '{document_id}' ({len(chunk_ids_to_update)} chunks) in collection '{collection_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to update document metadata '{document_id}' in collection '{collection_name}': {e}")
            return False

    def _serialize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, str | int | float | bool]:
        """Prepare metadata for ChromaDB storage by serializing complex types."""
        serialized = {}
        for key, value in metadata.items():
            if value is None:
                continue
            if isinstance(value, (list, dict)):
                serialized[key] = json.dumps(value)
            else:
                serialized[key] = value
        return serialized

    async def update_document(
        self, 
        collection_name: str, 
        document_id: str, 
        content: str, 
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Update a document's content and metadata in a transaction-like manner.
        """
        if not content or not content.strip():
            logger.error(f"Cannot update document '{document_id}': content is empty")
            return False

        current_chunks_backup = None
        
        try:
            client = self._get_client()
            collection = client.get_collection(collection_name)
            
            # 1. Get existing data for backup
            try:
                where_clause = self._build_where_clause({"doc_id": document_id})
                existing_data = collection.get(where=where_clause, include=["metadatas", "documents"])
                if existing_data["ids"]:
                    current_chunks_backup = existing_data
            except Exception as e:
                logger.warning(f"Failed to backup document '{document_id}' before update: {e}")
                # We proceed, but risk data loss if update fails. 
                # Ideally we might abort, but if the doc is corrupt/unreadable, maybe we want to overwrite it?
                # For now, we assume if we can't read it, we can't back it up.

            # 2. Prepare new data BEFORE deleting
            # Get current/merged metadata
            current_metadata = {}
            if current_chunks_backup:
                # Extract base metadata from first chunk (closest approximation)
                if current_chunks_backup["metadatas"]:
                    current_metadata = self._parse_metadata(current_chunks_backup["metadatas"][0])
            
            new_metadata = dict(current_metadata)
            new_metadata.update(metadata_updates)
            
            # Ensure critical fields
            new_metadata["doc_id"] = document_id
            new_metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Serialize metadata for storage
            storage_metadata = self._serialize_metadata(new_metadata)
            
            # Chunk content
            chunks = self._chunk_text(content)
            if not chunks:
                logger.error("Chunking resulted in failure (empty chunks)")
                return False

            ids = [f"{document_id}::c{i}" for i in range(len(chunks))]
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_meta = dict(storage_metadata)
                chunk_meta["seq"] = i
                chunk_meta["content_hash"] = self._sha1_hash(chunk)
                metadatas.append(chunk_meta)

            # 3. Delete existing
            await self.delete_document(collection_name, document_id)
            
            # 4. Upload new chunks
            try:
                collection.add(
                    ids=ids,
                    documents=chunks,
                    metadatas=metadatas,
                )
                logger.info(f"Successfully updated document '{document_id}' in collection '{collection_name}'")
                return True
                
            except Exception as upload_error:
                logger.error(f"Failed to upload new chunks for '{document_id}': {upload_error}")
                
                # 5. Rollback: Attempt to restore backup
                if current_chunks_backup:
                    logger.info(f"Attempting rollback for document '{document_id}'...")
                    try:
                        collection.add(
                            ids=current_chunks_backup["ids"],
                            documents=current_chunks_backup["documents"],
                            metadatas=current_chunks_backup["metadatas"]
                        )
                        logger.info(f"Rollback successful for '{document_id}'")
                    except Exception as rollback_error:
                        logger.critical(f"Rollback FAILED for '{document_id}'! Data loss may have occurred. Error: {rollback_error}")
                
                return False

        except Exception as e:
            logger.error(f"Failed to update document '{document_id}' in '{collection_name}': {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False


    async def get_latest_document_by_dimension(self, collection_name: str, dimension: str) -> Dict[str, Any]:
        """Get the latest document for a specific dimension efficiently."""
        client = self._get_client()
        collection = client.get_collection(collection_name)

        # 1. First, only query for metadatas to find the latest version
        # This avoids downloading huge document contents for all historical versions
        where_clause = self._build_where_clause({"dimension": dimension})
        result = collection.get(where=where_clause, include=["metadatas"])

        if not result["ids"]:
            raise ValueError(f"No documents found for dimension '{dimension}' in collection '{collection_name}'")

        # Group by document ID to find the latest one
        doc_metadata: Dict[str, dict] = {}

        for idx, chunk_id in enumerate(result["ids"]):
            metadata = result["metadatas"][idx] if result["metadatas"] else {}
            doc_id = metadata.get("doc_id", chunk_id.split("::")[0] if "::" in chunk_id else chunk_id)

            if doc_id not in doc_metadata:
                doc_metadata[doc_id] = {
                    "id": doc_id,
                    "uploaded_at": metadata.get("uploaded_at"),
                    "updated_at": metadata.get("updated_at"),
                    "is_latest": metadata.get("is_latest", False),
                    "title": metadata.get("title", "Untitled")
                }
            elif metadata.get("is_latest"):
                doc_metadata[doc_id]["is_latest"] = True

        # Find the latest document ID based on is_latest flag or timestamp
        latest_doc_id = None
        latest_info = None
        latest_timestamp = 0

        for doc_id, info in doc_metadata.items():
            if info["is_latest"]:
                latest_doc_id = doc_id
                latest_info = info
                break

            doc_ts = 0
            ts_str = info.get("updated_at") or info.get("uploaded_at")
            if ts_str:
                try:
                    doc_ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00')).timestamp()
                except (ValueError, AttributeError):
                    pass
            
            if not latest_doc_id or doc_ts > latest_timestamp:
                latest_doc_id = doc_id
                latest_info = info
                latest_timestamp = doc_ts

        if not latest_doc_id:
            raise ValueError(f"No valid documents found for dimension '{dimension}'")

        # 2. Now fetch only the chunks for the latest document ID
        # This is where we get the actual "documents" (content)
        where_latest = self._build_where_clause({"doc_id": latest_doc_id})
        latest_result = collection.get(where=where_latest, include=["metadatas", "documents"])
        
        if not latest_result["ids"]:
            # Fallback if doc_id filtering fails for some reason
            raise ValueError(f"Failed to fetch content for document '{latest_doc_id}'")

        chunks = []
        # Find some metadata to use for the result
        sample_metadata = latest_result["metadatas"][0] if latest_result["metadatas"] else {}

        for idx, chunk_id in enumerate(latest_result["ids"]):
            metadata = latest_result["metadatas"][idx] if latest_result["metadatas"] else {}
            document_text = latest_result["documents"][idx] if latest_result["documents"] else ""
            seq = metadata.get("seq", 0)
            chunks.append({"seq": seq, "content": document_text})

        # Final aggregation
        chunks.sort(key=lambda x: x["seq"])
        content = self._deduplicate_chunks([chunk["content"] for chunk in chunks])

        # Extract metadata fields only (exclude document structure fields)
        metadata_only = {
            k: v for k, v in sample_metadata.items()
            if k not in ["seq", "doc_id", "content_hash"]
        }
        parsed_metadata = self._parse_metadata(metadata_only)

        return {
            "id": latest_doc_id,
            "title": latest_info.get("title"),
            "collection_name": collection_name,
            "dimension": dimension,
            "metadata": parsed_metadata,
            "content": content,
            "chunk_count": len(chunks),
            "created_at": latest_info.get("updated_at") or latest_info.get("uploaded_at"),
        }


    async def get_latest_proof_points_by_company(self, company: str, collection_name: str = "proof_points") -> Dict[str, Any]:
        """Get the latest proof points document for a specific company efficiently."""
        client = self._get_client()
        collection = client.get_collection(collection_name)

        # 1. First, only query for metadatas to find the latest version
        # We filter for company and latest_version=True
        where_clause = self._build_where_clause({
            "company": company,
            "latest_version": True
        })
        result = collection.get(where=where_clause, include=["metadatas"])

        if not result["ids"]:
            raise ValueError(f"No latest proof points found for company '{company}'")

        # Find the latest document ID (there should be only one doc_id with latest_version=True per company)
        # but we use the first one found just in case.
        latest_doc_id = None
        
        # We need to collect all chunk IDs for this doc_id
        metadatas = result["metadatas"]
        first_metadata = metadatas[0] if metadatas else {}
        latest_doc_id = first_metadata.get("doc_id", result["ids"][0].split("::")[0] if "::" in result["ids"][0] else result["ids"][0])

        # 2. Now fetch all chunks for this specific document ID to get content
        where_latest = self._build_where_clause({"doc_id": latest_doc_id})
        latest_result = collection.get(where=where_latest, include=["metadatas", "documents"])
        
        if not latest_result["ids"]:
            raise ValueError(f"Failed to fetch content for proof points document '{latest_doc_id}'")

        chunks = []
        for idx, chunk_id in enumerate(latest_result["ids"]):
            metadata = latest_result["metadatas"][idx] if latest_result["metadatas"] else {}
            document_text = latest_result["documents"][idx] if latest_result["documents"] else ""
            seq = metadata.get("seq", 0)
            chunks.append({"seq": seq, "content": document_text})

        # Final aggregation
        chunks.sort(key=lambda x: x["seq"])
        content = self._deduplicate_chunks([chunk["content"] for chunk in chunks])

        # Use metadata from the first chunk for the result
        final_metadata = latest_result["metadatas"][0] if latest_result["metadatas"] else {}
        metadata_only = {
            k: v for k, v in final_metadata.items()
            if k not in ["seq", "doc_id", "content_hash"]
        }
        parsed_metadata = self._parse_metadata(metadata_only)

        return {
            "id": latest_doc_id,
            "title": final_metadata.get("title", "Untitled"),
            "collection_name": collection_name,
            "company": company,
            "metadata": parsed_metadata,
            "content": content,
            "chunk_count": len(chunks),
            "created_at": final_metadata.get("uploaded_at") or final_metadata.get("updated_at"),
        }
