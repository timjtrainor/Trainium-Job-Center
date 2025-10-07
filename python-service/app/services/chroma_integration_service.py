"""ChromaDB integration service for CrewAI workflows."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
from loguru import logger

from .chroma_manager import get_chroma_manager, CollectionType
from ..schemas.chroma import ChromaUploadResponse


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
        additional_metadata: Dict[str, Any] = None
    ) -> ChromaUploadResponse:
        """Add a resume document to the resumes collection.
        
        Standard Metadata Fields:
        - profile_id: str (required) - User profile identifier
        - section: str (default: "resume") - Document section/category
        - uploaded_at: str (auto) - Upload timestamp in ISO format
        - title: str (required) - Resume title
        
        Supports multiple versions but queries default to latest (ORDER BY uploaded_at DESC LIMIT 1).
        """

        # Auto-add uploaded_at if not provided
        if uploaded_at is None:
            uploaded_at = datetime.utcnow()

        metadata = {
            "profile_id": profile_id,
            "section": section,
            "uploaded_at": uploaded_at.isoformat(),
            "title": title
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        return await self.manager.upload_document(
            collection_name="resumes",
            title=title,
            document_text=content,
            metadata=metadata,
            tags=["resume", profile_id, section.lower()]
        )

    @staticmethod
    def derive_experience_key(
        resume_id: str,
        job_title: str,
        company_name: str,
        date_range: Optional[str] = None
    ) -> str:
        """Derive a deterministic key for work experience when explicit IDs are missing."""

        normalized = "||".join(
            part.strip().lower()
            for part in [resume_id or "", job_title or "", company_name or "", date_range or ""]
        )
        return hashlib.sha1(normalized.encode("utf-8")).hexdigest()

    async def add_resume_achievement(
        self,
        *,
        profile_id: str,
        resume_id: str,
        achievement_id: str,
        content: str,
        job_title: str,
        company_name: str,
        work_experience_id: Optional[str] = None,
        date_range: Optional[str] = None,
        always_include: bool = False,
        order_index: Optional[int] = None,
        themes: Optional[List[str]] = None,
        impact_scope: str = "",
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> ChromaUploadResponse:
        """Upload a resume achievement bullet with stable work experience metadata."""

        normalized_experience_id = work_experience_id or self.derive_experience_key(
            resume_id=resume_id,
            job_title=job_title,
            company_name=company_name,
            date_range=date_range or "",
        )

        metadata = {
            "profile_id": profile_id,
            "resume_id": resume_id,
            "achievement_id": achievement_id,
            "work_experience_id": normalized_experience_id,
            "job_title": job_title,
            "company_name": company_name,
            "date_range": date_range or "",
            "themes": themes or [],
            "always_include": always_include,
            "order_index": order_index if order_index is not None else -1,
            "impact_scope": impact_scope,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        safe_job_title = (job_title or "role").lower().replace(" ", "_")
        safe_company = (company_name or "company").lower().replace(" ", "_")
        experience_tag = normalized_experience_id or "experience"

        return await self.manager.upload_document(
            collection_name="resume_achievements",
            title=f"{job_title} @ {company_name} achievement",
            document_text=content,
            metadata=metadata,
            tags=["resume_achievement", resume_id, safe_job_title, safe_company, experience_tag]
        )

    async def query_resume_achievements(
        self,
        query: str,
        *,
        profile_id: Optional[str] = None,
        resume_id: Optional[str] = None,
        job_title: Optional[str] = None,
        work_experience_id: Optional[str] = None,
        n_results: int = 10,
    ) -> Dict[str, Any]:
        """Semantic search over resume achievements with optional metadata filters."""

        search_text = query.strip() or "resume achievement"
        where: Dict[str, Any] = {}

        if profile_id:
            where["profile_id"] = profile_id
        if resume_id:
            where["resume_id"] = resume_id
        if job_title:
            where["job_title"] = job_title
        if work_experience_id:
            where["work_experience_id"] = work_experience_id

        return await self.manager.search_collection(
            collection_name="resume_achievements",
            query=search_text,
            n_results=n_results,
            where=where or None,
        )

    async def add_user_expertise_document(
        self,
        *,
        profile_id: str,
        resume_id: str,
        expertise_area: str,
        content: str,
        skills: Optional[List[str]] = None,
        seniority: str = "",
        years_experience: Optional[str] = None,
        source: str = "",
        updated_at: Optional[datetime] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> ChromaUploadResponse:
        """Upload a user expertise slice for personalization-focused retrieval."""

        timestamp = (updated_at or datetime.utcnow()).isoformat()

        metadata = {
            "profile_id": profile_id,
            "resume_id": resume_id,
            "expertise_area": expertise_area,
            "skills": skills or [],
            "seniority": seniority,
            "years_experience": years_experience or "",
            "source": source,
            "updated_at": timestamp,
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        tag_area = expertise_area.lower().replace(" ", "_") if expertise_area else "expertise"

        return await self.manager.upload_document(
            collection_name="user_expertise",
            title=f"{expertise_area} expertise snapshot",
            document_text=content,
            metadata=metadata,
            tags=["user_expertise", resume_id, tag_area]
        )

    async def query_user_expertise(
        self,
        query: str,
        *,
        profile_id: Optional[str] = None,
        resume_id: Optional[str] = None,
        expertise_area: Optional[str] = None,
        n_results: int = 5,
    ) -> Dict[str, Any]:
        """Search expertise summaries for targeted skill retrieval."""

        search_text = query.strip() or "user expertise"
        where: Dict[str, Any] = {}

        if profile_id:
            where["profile_id"] = profile_id
        if resume_id:
            where["resume_id"] = resume_id
        if expertise_area:
            where["expertise_area"] = expertise_area

        return await self.manager.search_collection(
            collection_name="user_expertise",
            query=search_text,
            n_results=n_results,
            where=where or None,
        )

    async def add_company_voice_pattern(
        self,
        *,
        profile_id: str,
        resume_id: str,
        company_name: str,
        job_title: str,
        content: str,
        industry: str = "",
        tone_hint: str = "",
        keywords: Optional[List[str]] = None,
        accomplishment_count: int = 0,
        updated_at: Optional[datetime] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
        work_experience_id: Optional[str] = None,
    ) -> ChromaUploadResponse:
        """Upload tone exemplars derived from resume experiences."""

        timestamp = (updated_at or datetime.utcnow()).isoformat()
        normalized_experience_id = work_experience_id or self.derive_experience_key(
            resume_id=resume_id,
            job_title=job_title,
            company_name=company_name,
            date_range=(additional_metadata or {}).get("date_range") if additional_metadata else None,
        )

        metadata = {
            "profile_id": profile_id,
            "resume_id": resume_id,
            "work_experience_id": normalized_experience_id,
            "company_name": company_name,
            "job_title": job_title,
            "industry": industry,
            "tone_hint": tone_hint,
            "keywords": keywords or [],
            "accomplishment_count": accomplishment_count,
            "updated_at": timestamp,
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        safe_company = (company_name or "company").lower().replace(" ", "_")
        experience_tag = normalized_experience_id or "experience"

        return await self.manager.upload_document(
            collection_name="company_voice_patterns",
            title=f"{company_name} voice pattern",
            document_text=content,
            metadata=metadata,
            tags=["company_voice", resume_id, safe_company, experience_tag]
        )

    async def query_company_voice_patterns(
        self,
        query: str,
        *,
        profile_id: Optional[str] = None,
        resume_id: Optional[str] = None,
        company_name: Optional[str] = None,
        work_experience_id: Optional[str] = None,
        n_results: int = 5,
    ) -> Dict[str, Any]:
        """Search voice exemplars tied to resume experiences for a company."""

        search_text = query.strip() or "company voice"
        where: Dict[str, Any] = {}

        if profile_id:
            where["profile_id"] = profile_id
        if resume_id:
            where["resume_id"] = resume_id
        if company_name:
            where["company_name"] = company_name
        if work_experience_id:
            where["work_experience_id"] = work_experience_id

        return await self.manager.search_collection(
            collection_name="company_voice_patterns",
            query=search_text,
            n_results=n_results,
            where=where or None,
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