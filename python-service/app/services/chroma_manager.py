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
    CAREER_BRAND = "career_brand"
    PROOF_POINTS = "proof_points"
    RESUMES = "resumes"
    INTERVIEW_FEEDBACK = "interview_feedback"
    MARKET_INSIGHTS = "market_insights"
    TECHNICAL_SKILLS = "technical_skills"
    GENERIC_DOCUMENTS = "documents"
    CAREER_RESEARCH = "career_research"
    JOB_SEARCH_RESEARCH = "job_search_research"


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
            name="career_brand",
            collection_type=CollectionType.CAREER_BRAND,
            description="Personal career branding and positioning documents with versioning",
            chunk_size=300,
            chunk_overlap=50,
            metadata_schema={
                "profile_id": "str",
                "section": "str",
                "tags": "str",
                "title": "str",
                "type": "str",
                "status": "str",
                "is_latest": "bool",          # Version control flag
                "latest_version": "bool",      # Backwards compatibility flag
                "version": "int",              # Version number
                "timestamp": "str",            # ISO timestamp
                "uploaded_at": "str",          # Upload timestamp
                "updated_at": "str",
                "created_at": "str",
                "narrative_id": "str"          # Legacy identifier
            }
        ))

        # Proof points collection for role-specific accomplishments
        self.register_collection_config(ChromaCollectionConfig(
            name="proof_points",
            collection_type=CollectionType.PROOF_POINTS,
            description="Role-aligned proof points with version control",
            chunk_size=300,
            chunk_overlap=50,
            metadata_schema={
                "profile_id": "str",
                "role_title": "str",
                "company": "str",
                "title": "str",
                "status": "str",
                "impact_tags": "list",
                "type": "str",
                "is_latest": "bool",
                "latest_version": "bool",
                "version": "int",
                "timestamp": "str",
                "uploaded_at": "str",
                "updated_at": "str",
                "created_at": "str"
            }
        ))

        # Resumes collection with enriched metadata
        self.register_collection_config(ChromaCollectionConfig(
            name="resumes",
            collection_type=CollectionType.RESUMES,
            description="Versioned resumes linked to proof points and job targets",
            chunk_size=500,
            chunk_overlap=100,
            metadata_schema={
                "profile_id": "str",
                "job_target": "str",
                "section": "str",
                "title": "str",
                "status": "str",
                "selected_proof_points": "list",
                "type": "str",
                "is_latest": "bool",
                "latest_version": "bool",
                "version": "int",
                "timestamp": "str",
                "uploaded_at": "str",
                "updated_at": "str",
                "created_at": "str"
            }
        ))

        # Career research documents for users desired career research
        self.register_collection_config(ChromaCollectionConfig(
            name="career_research",
            collection_type=CollectionType.CAREER_RESEARCH,
            description="Personal career research documents for users desired career research",
            chunk_size=300,
            chunk_overlap=50,
            metadata_schema={
                "title": "str",
                "source": "str",
                "author": "str",
                "section": "str",
                "tags": "str",
                "type": "str"
            }
        ))

        # Job search research documents for users desired job search research
        self.register_collection_config(ChromaCollectionConfig(
            name="job_search_research",
            collection_type=CollectionType.JOB_SEARCH_RESEARCH,
            description="Holds research on candidate career trajectories, required skills, and industry trends.",
            chunk_size=300,
            chunk_overlap=50,
            metadata_schema={
                "section": "str",
                "source": "str",
                "author": "str",
                "tags": "str",
                "title": "str",
                "type": "str"
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

    async def _prepare_versioning(
        self,
        collection_name: str,
        unique_filters: Dict[str, Any]
    ) -> int:
        """Ensure only a single document is marked as latest and return the next version."""

        if not unique_filters:
            raise ValueError("unique_filters must contain at least one key")

        # Ensure collection exists before accessing it directly
        if not await self.ensure_collection_exists(collection_name):
            raise RuntimeError(f"Failed to ensure collection '{collection_name}' exists")

        client = self._get_client()
        collection = client.get_collection(collection_name)

        results = collection.get(where=unique_filters, include=["metadatas", "ids"])

        doc_chunks: Dict[str, Dict[str, Any]] = {}
        max_version = 0

        for chunk_id, metadata in zip(results.get("ids", []), results.get("metadatas", [])):
            if metadata is None:
                continue

            doc_id = metadata.get("doc_id")
            if not doc_id:
                continue

            entry = doc_chunks.setdefault(doc_id, {"ids": [], "metadatas": []})
            entry["ids"].append(chunk_id)
            entry["metadatas"].append(metadata)
            max_version = max(max_version, metadata.get("version", 0))

        for entry in doc_chunks.values():
            updated_metadatas = []
            for metadata in entry["metadatas"]:
                updated_metadata = dict(metadata)
                updated_metadata["is_latest"] = False
                updated_metadata["latest_version"] = False
                updated_metadatas.append(updated_metadata)

            if updated_metadatas:
                collection.update(ids=entry["ids"], metadatas=updated_metadatas)

        return max_version + 1

    async def _upload_versioned_document(
        self,
        collection_name: str,
        title: str,
        document_text: str,
        base_metadata: Dict[str, Any],
        unique_keys: List[str],
        tags: Optional[List[str]] = None
    ) -> ChromaUploadResponse:
        """Upload a document ensuring unique latest version per key set."""

        if not unique_keys:
            raise ValueError("unique_keys must not be empty")

        unique_filters = {key: base_metadata.get(key) for key in unique_keys if base_metadata.get(key) is not None}

        if len(unique_filters) != len(unique_keys):
            missing = [key for key in unique_keys if key not in unique_filters]
            raise ValueError(f"Missing metadata required for versioning: {', '.join(missing)}")

        next_version = await self._prepare_versioning(collection_name, unique_filters)

        timestamp = datetime.now(timezone.utc).isoformat()
        metadata = dict(base_metadata)
        metadata.update({
            "version": next_version,
            "is_latest": True,
            "latest_version": True,
            "timestamp": timestamp,
            "updated_at": timestamp,
        })
        metadata.setdefault("uploaded_at", timestamp)
        metadata.setdefault("created_at", timestamp)

        return await self.upload_document(
            collection_name=collection_name,
            title=title,
            document_text=document_text,
            metadata=metadata,
            tags=tags
        )
    
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

    async def upload_career_brand_document(
        self,
        section: str,
        content: str,
        title: str,
        narrative_id: str
    ) -> ChromaUploadResponse:
        """
        Upload a career brand document with automatic versioning.

        This method ensures only one "latest" version exists per section and narrative.
        Previous versions are marked as not latest, but preserved for audit trail.
        """
        try:
            metadata = {
                "section": section,
                "profile_id": narrative_id,
                "narrative_id": narrative_id,
                "title": title,
                "status": "active",
                "type": "career_brand_document"
            }

            result = await self._upload_versioned_document(
                collection_name="career_brand",
                title=title,
                document_text=content,
                base_metadata=metadata,
                unique_keys=["profile_id", "section"],
                tags=["career_brand", section, f"profile:{narrative_id}"]
            )

            if result.success:
                latest_doc = await self.find_latest_by_section_and_narrative(section, narrative_id)
                version_number = latest_doc.get("version", 1) if latest_doc else 1
                logger.info(
                    f"Successfully uploaded career brand document: {section} v{version_number} "
                    f"for narrative {narrative_id}"
                )
            else:
                logger.error(f"Failed to upload career brand document: {result.message}")

            return result

        except Exception as e:
            error_msg = f"Failed to upload versioned career brand document for {section}: {str(e)}"
            logger.error(error_msg)
            return ChromaUploadResponse(
                success=False,
                message=error_msg,
                collection_name="career_brand",
                document_id="",
                chunks_created=0,
                error_type="VERSIONING_ERROR"
            )

    async def upload_proof_point_document(
        self,
        profile_id: str,
        role_title: str,
        job_title: str,
        location: str,
        start_date: str,
        end_date: str,
        is_current: bool,
        company: str,
        content: str,
        title: str,
        status: str = "draft",
        impact_tags: Optional[List[str]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> ChromaUploadResponse:
        """Upload a proof point document ensuring unique latest per role and company."""

        try:
            metadata = {
                "profile_id": profile_id,
                "role_title": role_title,
                "job_title": job_title,
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "is_current": is_current,
                "company": company,
                "title": title,
                "status": status,
                "impact_tags": impact_tags or [],
                "type": "proof_point_document"
            }

            if additional_metadata:
                metadata.update(additional_metadata)

            tags = [
                "proof_point",
                profile_id,
                role_title,
                company
            ]

            return await self._upload_versioned_document(
                collection_name="proof_points",
                title=title,
                document_text=content,
                base_metadata=metadata,
                unique_keys=[
                    "profile_id",
                    "company",
                    "job_title",
                    "location",
                    "start_date",
                    "end_date",
                    "is_current",
                ],
                tags=tags
            )

        except Exception as e:
            error_msg = f"Failed to upload proof point document: {str(e)}"
            logger.error(error_msg)
            return ChromaUploadResponse(
                success=False,
                message=error_msg,
                collection_name="proof_points",
                document_id="",
                chunks_created=0,
                error_type="VERSIONING_ERROR"
            )

    async def upload_resume_document(
        self,
        profile_id: str,
        job_target: str,
        content: str,
        title: str,
        status: str = "draft",
        selected_proof_points: Optional[List[str]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> ChromaUploadResponse:
        """Upload a resume with versioning tied to profile and job target."""

        try:
            metadata = {
                "profile_id": profile_id,
                "job_target": job_target,
                "section": "resume",
                "title": title,
                "status": status,
                "selected_proof_points": selected_proof_points or [],
                "type": "resume_document"
            }

            if additional_metadata:
                metadata.update(additional_metadata)

            tags = [
                "resume",
                profile_id,
                job_target
            ]

            return await self._upload_versioned_document(
                collection_name="resumes",
                title=title,
                document_text=content,
                base_metadata=metadata,
                unique_keys=["profile_id", "job_target"],
                tags=tags
            )

        except Exception as e:
            error_msg = f"Failed to upload resume document: {str(e)}"
            logger.error(error_msg)
            return ChromaUploadResponse(
                success=False,
                message=error_msg,
                collection_name="resumes",
                document_id="",
                chunks_created=0,
                error_type="VERSIONING_ERROR"
            )

    async def find_latest_by_section_and_narrative(
        self,
        section: str,
        narrative_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find the latest document for a specific section and narrative.

        Returns the most recent document that has latest_version=true.
        """
        try:
            if not await self.ensure_collection_exists("career_brand"):
                return None

            client = self._get_client()
            collection = client.get_collection("career_brand")

            def _get_latest(where_clause: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                results = collection.get(
                    where=where_clause,
                    include=["metadatas", "documents", "ids"]
                )

                metadatas = results.get("metadatas", []) or []
                documents = results.get("documents", []) or []

                if not metadatas:
                    return None

                aggregated: Dict[str, Dict[str, Any]] = {}

                for idx, metadata in enumerate(metadatas):
                    if metadata is None:
                        continue

                    doc_id = metadata.get("doc_id")
                    if not doc_id:
                        continue

                    document = documents[idx] if idx < len(documents) else ""

                    entry = aggregated.setdefault(doc_id, {
                        "document_id": doc_id,
                        "content": document,
                        "metadata": metadata,
                        "version": metadata.get("version", 1)
                    })

                    # Prefer the lowest sequence chunk for representative content
                    current_seq = entry["metadata"].get("seq", 0)
                    new_seq = metadata.get("seq", 0)
                    if new_seq < current_seq:
                        entry["content"] = document
                        entry["metadata"] = metadata
                        entry["version"] = metadata.get("version", entry["version"])

                if not aggregated:
                    return None

                return max(aggregated.values(), key=lambda item: item["version"])

            latest = _get_latest({
                "section": section,
                "narrative_id": narrative_id,
                "is_latest": True
            })

            if latest:
                return latest

            # Backwards compatibility for records that still use latest_version
            return _get_latest({
                "section": section,
                "narrative_id": narrative_id,
                "latest_version": True
            })

        except Exception as e:
            logger.error(
                f"Failed to find latest document for section '{section}' "
                f"narrative '{narrative_id}': {e}"
            )
            return None

    async def mark_version_not_latest(self, document_id: str) -> bool:
        """
        Mark a document version as not latest.

        This updates the metadata to remove the latest_version flag.
        Used when a newer version is uploaded.
        """
        try:
            client = self._get_client()
            collection = client.get_collection("career_brand")

            # Get all chunks for this document (they share the doc_id)
            where_filter = {"doc_id": document_id}

            # Query to find all chunks for this document
            results = collection.get(where=where_filter, include=["metadatas"])

            if not results["metadatas"]:
                logger.warning(f"No chunks found for document {document_id}")
                return False

            # Update each chunk's metadata to remove latest_version flag
            chunk_ids = results["ids"]
            updated_metadatas = []

            for metadata in results["metadatas"]:
                updated_metadata = dict(metadata)  # Make a copy
                updated_metadata["latest_version"] = False  # Remove latest flag
                updated_metadata["is_latest"] = False
                updated_metadatas.append(updated_metadata)

            # Update the collection in batch
            collection.update(
                ids=chunk_ids,
                metadatas=updated_metadatas
            )

            logger.info(f"Marked document {document_id} as not latest")
            return True

        except Exception as e:
            logger.error(f"Failed to mark document {document_id} as not latest: {e}")
            return False

    async def get_career_brand_version_history(
        self,
        section: str,
        narrative_id: str,
        include_content: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get version history for a career brand section.

        Returns all versions (old and latest) for audit and review purposes.
        """
        try:
            base_where = {
                "section": section,
                "narrative_id": narrative_id,
            }

            # Try querying with the profile_id-aware filter first, but fall back
            # to the legacy filter when no documents are returned. Legacy
            # records did not populate profile_id so we need to remain backward
            # compatible with that data.
            where_clauses = [
                {**base_where, "profile_id": narrative_id},
                base_where,
            ]

            result = None
            for where_clause in where_clauses:
                result = await self.search_collection(
                    collection_name="career_brand",
                    query="",  # Empty query to get all
                    n_results=50,  # Get many potential versions
                    where=where_clause,
                    include_metadata=True
                )

                if result["success"] and result["documents"]:
                    break

            if not result or not result["success"] or not result["documents"]:
                return []

            # Process and deduplicate by document_id (since multiple chunks per doc)
            version_map = {}

            for i, (content, metadata) in enumerate(
                zip(result["documents"], result["metadatas"])
            ):
                doc_id = metadata["doc_id"]
                version = metadata.get("version", 1)

                if doc_id not in version_map:
                    version_map[doc_id] = {
                        "document_id": doc_id,
                        "version": version,
                        "latest_version": metadata.get(
                            "is_latest",
                            metadata.get("latest_version", False)
                        ),
                        "timestamp": metadata.get("timestamp"),
                        "uploaded_at": metadata.get("uploaded_at"),
                        "title": metadata.get("title"),
                        "profile_id": metadata.get("profile_id", narrative_id),
                        "content_preview": content[:200] + "..." if len(content) > 200 else content
                    }

                    if include_content:
                        version_map[doc_id]["full_content"] = content

            # Sort by version number (descending) to show latest first
            versions = list(version_map.values())
            versions.sort(key=lambda x: x["version"], reverse=True)

            return versions

        except Exception as e:
            logger.error(
                f"Failed to get version history for {section}/{narrative_id}: {e}"
            )
            return []


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
