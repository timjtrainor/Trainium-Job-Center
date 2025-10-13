"""ChromaDB integration service for CrewAI workflows."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from .chroma_manager import get_chroma_manager, CollectionType
from ..schemas.chroma import ChromaUploadRequest, ChromaUploadResponse


class ChromaIntegrationService:
    """Service for integrating ChromaDB with CrewAI workflows."""
    
    def __init__(self):
        """Initialize the ChromaDB integration service."""
        self.manager = get_chroma_manager()
    
    async def initialize(self):
        """Initialize the service and ensure default collections exist."""
        await self.manager.initialize()
        
        # Ensure all default collections exist
        for config in self.manager.list_registered_collections():
            await self.manager.ensure_collection_exists(config.name)
            logger.info(f"Collection '{config.name}' is ready for CrewAI integration")
    
    async def add_job_posting(
        self,
        title: str,
        company: str,
        description: str,
        location: str = "",
        salary_range: str = "",
        skills: List[str] = None,
        job_type: str = "",
        experience_level: str = "",
        additional_metadata: Dict[str, Any] = None
    ) -> ChromaUploadResponse:
        """Add a job posting to the job_postings collection."""
        
        metadata = {
            "company": company,
            "location": location,
            "salary_range": salary_range,
            "skills": skills or [],
            "job_type": job_type,
            "experience_level": experience_level
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return await self.manager.upload_document(
            collection_name="job_postings",
            title=title,
            document_text=description,
            metadata=metadata,
            tags=["job_posting", company.lower().replace(" ", "_")]
        )
    
    async def add_company_profile(
        self,
        company_name: str,
        description: str,
        industry: str = "",
        size: str = "",
        culture_info: str = "",
        benefits: List[str] = None,
        values: List[str] = None,
        additional_metadata: Dict[str, Any] = None
    ) -> ChromaUploadResponse:
        """Add a company profile to the company_profiles collection."""

        # Combine description with culture info if available
        full_description = description
        if culture_info:
            full_description += f"\n\nCulture: {culture_info}"

        metadata = {
            "company_name": company_name,
            "industry": industry,
            "size": size,
            "benefits": benefits or [],
            "values": values or []
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        return await self.manager.upload_document(
            collection_name="company_profiles",
            title=f"{company_name} Company Profile",
            document_text=full_description,
            metadata=metadata,
            tags=["company_profile", company_name.lower().replace(" ", "_"), industry.lower()]
        )
    
    async def add_career_brand_document(
        self,
        title: str,
        content: str,
        profile_id: str,
        section: str,
        source: str = "",
        author: str = "",
        uploaded_at: Optional[datetime] = None,
        additional_metadata: Dict[str, Any] = None
    ) -> ChromaUploadResponse:
        """Add a career branding document to the career_brand collection.
        
        Standard Metadata Fields:
        - profile_id: str (required) - User profile identifier
        - section: str (required) - Document section/category
        - uploaded_at: str (auto) - Upload timestamp in ISO format
        - source: str (optional) - Document source
        - author: str (optional) - Document author
        """

        # Auto-add uploaded_at if not provided
        if uploaded_at is None:
            uploaded_at = datetime.utcnow()

        metadata = {
            "profile_id": profile_id,
            "section": section,
            "uploaded_at": uploaded_at.isoformat(),
            "source": source,
            "author": author
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        return await self.manager.upload_document(
            collection_name="career_brand",
            title=title,
            document_text=content,
            metadata=metadata,
            tags=["career_brand", profile_id, section.lower()]
        )

    async def add_career_path_document(
        self,
        title: str,
        content: str,
        profile_id: str,
        section: str,
        source: str = "",
        author: str = "",
        uploaded_at: Optional[datetime] = None,
        additional_metadata: Dict[str, Any] = None
    ) -> ChromaUploadResponse:
        """Add a career path document to the career_paths collection.
        
        Standard Metadata Fields:
        - profile_id: str (required) - User profile identifier
        - section: str (required) - Document section/category
        - uploaded_at: str (auto) - Upload timestamp in ISO format
        - source: str (optional) - Document source
        - author: str (optional) - Document author
        """

        # Auto-add uploaded_at if not provided
        if uploaded_at is None:
            uploaded_at = datetime.utcnow()

        metadata = {
            "profile_id": profile_id,
            "section": section,
            "uploaded_at": uploaded_at.isoformat(),
            "source": source,
            "author": author
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        return await self.manager.upload_document(
            collection_name="career_paths",
            title=title,
            document_text=content,
            metadata=metadata,
            tags=["career_paths", profile_id, section.lower()]
        )

    async def add_job_search_strategies_document(
        self,
        title: str,
        content: str,
        profile_id: str,
        section: str,
        source: str = "",
        author: str = "",
        uploaded_at: Optional[datetime] = None,
        additional_metadata: Dict[str, Any] = None
    ) -> ChromaUploadResponse:
        """Add a job search strategy document to the job_search_strategies collection.
        
        Standard Metadata Fields:
        - profile_id: str (required) - User profile identifier
        - section: str (required) - Document section/category
        - uploaded_at: str (auto) - Upload timestamp in ISO format
        - source: str (optional) - Document source
        - author: str (optional) - Document author
        """

        # Auto-add uploaded_at if not provided
        if uploaded_at is None:
            uploaded_at = datetime.utcnow()

        metadata = {
            "profile_id": profile_id,
            "section": section,
            "uploaded_at": uploaded_at.isoformat(),
            "source": source,
            "author": author
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        return await self.manager.upload_document(
            collection_name="job_search_strategies",
            title=title,
            document_text=content,
            metadata=metadata,
            tags=["job_search_strategies", profile_id, section.lower()]
        )

    async def add_resume_document(
        self,
        title: str,
        content: str,
        profile_id: str,
        section: str = "resume",
        uploaded_at: Optional[datetime] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
        *,
        job_target: Optional[str] = None,
        status: Optional[str] = None,
        selected_proof_points: Optional[List[str]] = None,
        status_transitions: Optional[List[Dict[str, Any]]] = None,
        approved_by: Optional[str] = None,
        approved_at: Optional[datetime] = None,
        approval_notes: Optional[str] = None,
        version: Optional[int] = None,
        is_latest: Optional[bool] = None
    ) -> ChromaUploadResponse:
        """Add or update a resume document with enriched metadata.

        Supports version rollover by delegating to ``ChromaManager.upload_resume_document``.
        """

        metadata = self._prepare_resume_rollover_metadata(
            profile_id=profile_id,
            section=section,
            uploaded_at=uploaded_at,
            additional_metadata=additional_metadata,
            job_target=job_target,
            status=status,
            selected_proof_points=selected_proof_points,
            status_transitions=status_transitions,
            approved_by=approved_by,
            approved_at=approved_at,
            approval_notes=approval_notes,
            version=version,
            is_latest=is_latest,
            title=title
        )

        resolved_job_target = metadata.get("job_target")

        if resolved_job_target:
            sanitized_metadata = dict(metadata)
            sanitized_metadata.pop("job_target", None)
            resolved_status = sanitized_metadata.get("status", "draft")
            resolved_selected_points = sanitized_metadata.get("selected_proof_points")

            return await self.manager.upload_resume_document(
                profile_id=profile_id,
                job_target=resolved_job_target,
                content=content,
                title=title,
                status=resolved_status,
                selected_proof_points=resolved_selected_points,
                additional_metadata=sanitized_metadata
            )

        fallback_tags = ["resume", profile_id]
        section_tag = metadata.get("section")
        if section_tag:
            fallback_tags.append(section_tag)

        return await self.manager.upload_document(
            collection_name="resumes",
            title=title,
            document_text=content,
            metadata=metadata,
            tags=fallback_tags
        )

    async def update_resume_document(
        self,
        document_id: str,
        *,
        status: Optional[str] = None,
        selected_proof_points: Optional[List[str]] = None,
        approved_by: Optional[str] = None,
        approved_at: Optional[datetime] = None,
        approval_notes: Optional[str] = None,
        status_transitions: Optional[List[Dict[str, Any]]] = None,
        is_latest: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Update metadata for an existing resume document."""

        try:
            if not await self.manager.ensure_collection_exists("resumes"):
                return {
                    "success": False,
                    "message": "Resumes collection is unavailable",
                    "document_id": document_id,
                }

            client = self.manager._get_client()
            collection = client.get_collection("resumes")

            results = collection.get(
                where={"doc_id": document_id},
                include=["metadatas", "ids"]
            )

            metadatas = results.get("metadatas") or []
            chunk_ids = results.get("ids") or []

            if not metadatas or not chunk_ids:
                return {
                    "success": False,
                    "message": f"Resume document '{document_id}' was not found",
                    "document_id": document_id,
                }

            updated_at = datetime.utcnow().isoformat()
            base_metadata = metadatas[0] or {}
            updated_metadatas: List[Dict[str, Any]] = []

            normalized_transitions: Optional[List[Dict[str, Any]]] = None
            if status_transitions is not None:
                normalized_transitions = []
                for transition in status_transitions:
                    normalized = dict(transition)
                    if "changed_at" in normalized:
                        normalized["changed_at"] = self._normalize_datetime(
                            normalized["changed_at"]
                        )
                    normalized_transitions.append(normalized)

            for metadata in metadatas:
                updated_metadata = dict(metadata or {})
                previous_status = updated_metadata.get("status")

                if status is not None:
                    updated_metadata["status"] = status
                    if status != previous_status:
                        transitions = list(updated_metadata.get("status_transitions") or [])
                        transitions.append({
                            "from": previous_status,
                            "to": status,
                            "changed_at": updated_at,
                            "changed_by": approved_by or updated_metadata.get("approved_by"),
                        })
                        updated_metadata["status_transitions"] = transitions

                if normalized_transitions is not None:
                    updated_metadata["status_transitions"] = normalized_transitions

                if selected_proof_points is not None:
                    updated_metadata["selected_proof_points"] = list(selected_proof_points)

                if approved_by is not None:
                    updated_metadata["approved_by"] = approved_by

                if approved_at is not None:
                    updated_metadata["approved_at"] = self._normalize_datetime(approved_at)

                if approval_notes is not None:
                    updated_metadata["approval_notes"] = approval_notes

                if is_latest is not None:
                    updated_metadata["is_latest"] = is_latest
                    updated_metadata["latest_version"] = is_latest

                updated_metadata["updated_at"] = updated_at

                updated_metadatas.append(updated_metadata)

            collection.update(ids=chunk_ids, metadatas=updated_metadatas)

            if is_latest:
                unique_filters = {
                    key: base_metadata.get(key)
                    for key in ("profile_id", "job_target")
                    if base_metadata.get(key) is not None
                }

                if unique_filters:
                    existing = collection.get(
                        where=unique_filters,
                        include=["metadatas", "ids"]
                    )

                    demote_ids: List[str] = []
                    demote_metadatas: List[Dict[str, Any]] = []

                    for chunk_id, metadata in zip(
                        existing.get("ids", []), existing.get("metadatas", [])
                    ):
                        if metadata is None or metadata.get("doc_id") == document_id:
                            continue

                        demoted_metadata = dict(metadata)
                        if demoted_metadata.get("is_latest"):
                            demoted_metadata["is_latest"] = False
                        if demoted_metadata.get("latest_version"):
                            demoted_metadata["latest_version"] = False
                        demoted_metadata["updated_at"] = updated_at

                        demote_ids.append(chunk_id)
                        demote_metadatas.append(demoted_metadata)

                    if demote_ids:
                        collection.update(ids=demote_ids, metadatas=demote_metadatas)

            return {
                "success": True,
                "message": "Resume metadata updated",
                "document_id": document_id,
                "metadata": updated_metadatas[0],
            }

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to update resume document '{document_id}': {exc}")
            return {
                "success": False,
                "message": str(exc),
                "document_id": document_id,
            }

    def _prepare_resume_rollover_metadata(
        self,
        *,
        profile_id: str,
        section: str,
        uploaded_at: Optional[datetime],
        additional_metadata: Optional[Dict[str, Any]],
        job_target: Optional[str],
        status: Optional[str],
        selected_proof_points: Optional[List[str]],
        status_transitions: Optional[List[Dict[str, Any]]],
        approved_by: Optional[str],
        approved_at: Optional[datetime],
        approval_notes: Optional[str],
        version: Optional[int],
        is_latest: Optional[bool],
        title: str
    ) -> Dict[str, Any]:
        """Normalize resume metadata before delegating to the manager."""

        metadata: Dict[str, Any] = {
            "profile_id": profile_id,
            "section": section,
            "title": title
        }

        if additional_metadata:
            metadata.update(dict(additional_metadata))

        resolved_job_target = job_target or metadata.get("job_target")
        if resolved_job_target:
            metadata["job_target"] = resolved_job_target

        timestamp = self._normalize_datetime(uploaded_at) or metadata.get("uploaded_at")
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()
        metadata["uploaded_at"] = timestamp

        resolved_status = status or metadata.get("status") or "draft"
        metadata["status"] = resolved_status

        if selected_proof_points is not None:
            metadata["selected_proof_points"] = list(selected_proof_points)
        else:
            metadata.setdefault("selected_proof_points", [])

        if status_transitions is not None:
            metadata["status_transitions"] = list(status_transitions)
        else:
            metadata.setdefault("status_transitions", [])

        if approved_by is not None:
            metadata["approved_by"] = approved_by
        if approved_at is not None:
            metadata["approved_at"] = self._normalize_datetime(approved_at)
        elif "approved_at" in metadata and metadata["approved_at"] is not None:
            metadata["approved_at"] = self._normalize_datetime(metadata["approved_at"])
        if approval_notes is not None:
            metadata["approval_notes"] = approval_notes

        if version is not None:
            metadata["version"] = version
        if is_latest is not None:
            metadata["is_latest"] = is_latest

        return metadata

    def _normalize_datetime(self, value: Optional[Any]) -> Optional[str]:
        """Convert datetime-like values to ISO strings."""

        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        raise TypeError(f"Unsupported datetime value type: {type(value)}")

    def _prepare_proof_point_rollover_metadata(
        self,
        *,
        job_metadata: Optional[Dict[str, Any]],
        job_title: Optional[str],
        location: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
        is_current: Optional[bool],
        status: str,
        uploaded_at: Optional[datetime],
        status_transitions: Optional[List[Dict[str, Any]]],
        impact_tags: Optional[List[str]],
        additional_metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Normalize proof point metadata before delegating to the manager."""

        metadata: Dict[str, Any] = {}
        if additional_metadata:
            metadata.update(dict(additional_metadata))

        if job_metadata:
            for key, value in job_metadata.items():
                if value is not None:
                    metadata[f"job_{key}"] = value

        def _stringify(value: Optional[Any]) -> str:
            if value is None:
                return ""
            if isinstance(value, datetime):
                return value.isoformat()
            return str(value)

        metadata["job_title"] = _stringify(job_title) or metadata.get("job_title") or ""
        metadata["location"] = _stringify(location) or metadata.get("location") or ""
        metadata["start_date"] = _stringify(start_date) or metadata.get("start_date") or ""
        metadata["end_date"] = _stringify(end_date) or metadata.get("end_date") or ""
        metadata["is_current"] = (
            bool(is_current)
            if is_current is not None
            else bool(metadata.get("is_current", False))
        )

        timestamp = self._normalize_datetime(uploaded_at) or metadata.get("uploaded_at")
        if not timestamp:
            timestamp = datetime.utcnow().isoformat()
        metadata["uploaded_at"] = timestamp

        metadata["status"] = status

        if status_transitions is not None:
            metadata["status_transitions"] = list(status_transitions)
        else:
            metadata.setdefault("status_transitions", [])

        if impact_tags is not None:
            metadata.setdefault("impact_tags", list(impact_tags))

        return metadata

    async def create_proof_point_for_job(
        self,
        profile_id: str,
        role_title: str,
        company: str,
        content: str,
        title: str,
        *,
        job_title: Optional[str] = None,
        location: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_current: Optional[bool] = None,
        job_metadata: Optional[Dict[str, Any]] = None,
        status: str = "draft",
        impact_tags: Optional[List[str]] = None,
        uploaded_at: Optional[datetime] = None,
        status_transitions: Optional[List[Dict[str, Any]]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> ChromaUploadResponse:
        """Create a proof point tied to a specific job context."""

        metadata = self._prepare_proof_point_rollover_metadata(
            job_metadata=job_metadata,
            job_title=job_title or role_title,
            location=location,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            status=status,
            uploaded_at=uploaded_at,
            status_transitions=status_transitions,
            impact_tags=impact_tags,
            additional_metadata=additional_metadata
        )

        return await self.manager.upload_proof_point_document(
            profile_id=profile_id,
            role_title=role_title,
            job_title=job_title or role_title,
            location=location or "",
            start_date=start_date or "",
            end_date=end_date or "",
            is_current=is_current if is_current is not None else False,
            company=company,
            content=content,
            title=title,
            status=status,
            impact_tags=impact_tags,
            additional_metadata=metadata
        )

    async def update_proof_point_for_job(
        self,
        profile_id: str,
        role_title: str,
        company: str,
        content: str,
        title: str,
        *,
        job_title: Optional[str] = None,
        location: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_current: Optional[bool] = None,
        job_metadata: Optional[Dict[str, Any]] = None,
        status: str = "draft",
        impact_tags: Optional[List[str]] = None,
        uploaded_at: Optional[datetime] = None,
        status_transitions: Optional[List[Dict[str, Any]]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
        version: Optional[int] = None,
        is_latest: Optional[bool] = None
    ) -> ChromaUploadResponse:
        """Update an existing proof point with new metadata and rollover handling."""

        metadata = self._prepare_proof_point_rollover_metadata(
            job_metadata=job_metadata,
            job_title=job_title or role_title,
            location=location,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            status=status,
            uploaded_at=uploaded_at,
            status_transitions=status_transitions,
            impact_tags=impact_tags,
            additional_metadata=additional_metadata
        )

        if version is not None:
            metadata["version"] = version
        if is_latest is not None:
            metadata["is_latest"] = is_latest

        return await self.manager.upload_proof_point_document(
            profile_id=profile_id,
            role_title=role_title,
            job_title=job_title or role_title,
            location=location or "",
            start_date=start_date or "",
            end_date=end_date or "",
            is_current=is_current if is_current is not None else False,
            company=company,
            content=content,
            title=title,
            status=status,
            impact_tags=impact_tags,
            additional_metadata=metadata
        )

    async def bulk_upload_job_postings(
        self, 
        job_postings: List[Dict[str, Any]]
    ) -> List[ChromaUploadResponse]:
        """Bulk upload multiple job postings."""
        results = []
        
        for job_data in job_postings:
            try:
                result = await self.add_job_posting(
                    title=job_data.get("title", ""),
                    company=job_data.get("company", ""),
                    description=job_data.get("description", ""),
                    location=job_data.get("location", ""),
                    salary_range=job_data.get("salary_range", ""),
                    skills=job_data.get("skills", []),
                    job_type=job_data.get("job_type", ""),
                    experience_level=job_data.get("experience_level", ""),
                    additional_metadata=job_data.get("metadata", {})
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to upload job posting '{job_data.get('title', 'Unknown')}': {e}")
                results.append(ChromaUploadResponse(
                    success=False,
                    message=f"Failed to upload: {str(e)}",
                    collection_name="job_postings",
                    document_id="",
                    chunks_created=0,
                    error_type="BULK_UPLOAD_ERROR"
                ))
        
        return results
    
    async def search_for_crew_context(
        self,
        query: str,
        collections: List[str] = None,
        n_results: int = 5,
        profile_id: Optional[str] = None,
        section: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search ChromaDB to provide context for CrewAI agents with optional profile_id and section filtering.
        
        Always retrieves the latest version when multiple documents exist for the same profile_id and section.
        """
        
        if collections is None:
            # Default to searching job-related collections
            collections = ["job_postings", "company_profiles"]
        
        # Build where clause for filtering
        where_clause = {}
        if profile_id:
            where_clause["profile_id"] = profile_id
        if section:
            where_clause["section"] = section
        
        # For collections that support versioning, we'll need to filter for latest versions
        # This will be handled by the manager's search functionality
        result = await self.manager.search_across_collections(
            query=query,
            collection_names=collections,
            n_results=n_results,
            include_metadata=True,
            where=where_clause if where_clause else None
        )
        
        # Format results for CrewAI consumption
        formatted_context = {
            "query": query,
            "collections_searched": collections,
            "filters_applied": {
                "profile_id": profile_id,
                "section": section
            },
            "found_relevant_content": result.get("success", False),
            "context_summary": [],
            "detailed_results": result.get("results", {})
        }
        
        if result.get("success", False):
            for collection_name, collection_result in result.get("results", {}).items():
                if collection_result.get("success", False) and collection_result.get("documents"):
                    documents = collection_result.get("documents", [])
                    
                    # Sort by uploaded_at to get latest versions first if available
                    metadatas = collection_result.get("metadatas", [])
                    if metadatas and any("uploaded_at" in meta for meta in metadatas):
                        # Combine documents with metadata and sort by uploaded_at
                        doc_meta_pairs = list(zip(documents, metadatas))
                        doc_meta_pairs.sort(
                            key=lambda x: x[1].get("uploaded_at", ""), 
                            reverse=True
                        )
                        documents = [pair[0] for pair in doc_meta_pairs]
                    
                    formatted_context["context_summary"].append({
                        "collection": collection_name,
                        "num_results": len(documents),
                        "preview": documents[0][:200] + "..." if documents else ""
                    })
        
        return formatted_context
    
    async def get_collection_status(self) -> Dict[str, Any]:
        """Get the status of all collections for monitoring."""
        collections = await self.manager.list_all_collections()
        registered_configs = self.manager.list_registered_collections()
        
        status = {
            "total_collections": len(collections),
            "registered_types": len(registered_configs),
            "collections": [],
            "registered_configs": []
        }
        
        for collection in collections:
            status["collections"].append({
                "name": collection.name,
                "count": collection.count,
                "metadata": collection.metadata
            })
        
        for config in registered_configs:
            status["registered_configs"].append({
                "name": config.name,
                "type": config.collection_type.value,
                "description": config.description,
                "chunk_size": config.chunk_size
            })
        
        return status
    
    async def prepare_crew_rag_context(
        self,
        job_posting: Dict[str, Any],
        profile_id: Optional[str] = None,
        section: Optional[str] = None,
        additional_queries: List[str] = None
    ) -> Dict[str, Any]:
        """Prepare comprehensive RAG context for job posting review crews with profile_id and section filtering.
        
        Always retrieves the latest version when multiple documents exist for the same profile_id and section.
        """
        
        # Extract key information from job posting
        job_title = job_posting.get("title", "")
        company = job_posting.get("company", "")
        description = job_posting.get("description", "")
        
        # Build search queries
        queries = [
            f"{job_title} {company}",  # Specific job and company match
            job_title,  # General job title search
        ]
        
        if additional_queries:
            queries.extend(additional_queries)
        
        rag_context = {
            "job_posting": job_posting,
            "profile_id": profile_id,
            "section": section,
            "search_results": {},
            "context_summary": []
        }
        
        # Search for relevant context
        for query in queries:
            search_collections = ["job_postings", "company_profiles"]
            if profile_id:
                search_collections.extend(["career_brand", "career_paths", "job_search_strategies", "resumes"])
            
            context = await self.search_for_crew_context(
                query=query,
                collections=search_collections,
                n_results=3,
                profile_id=profile_id,
                section=section
            )
            
            rag_context["search_results"][query] = context
            
            if context.get("found_relevant_content"):
                rag_context["context_summary"].extend(context.get("context_summary", []))
        
        return rag_context


# Global service instance
_chroma_integration_service: Optional[ChromaIntegrationService] = None


def get_chroma_integration_service() -> ChromaIntegrationService:
    """Get the global ChromaDB integration service instance."""
    global _chroma_integration_service
    if _chroma_integration_service is None:
        _chroma_integration_service = ChromaIntegrationService()
    return _chroma_integration_service