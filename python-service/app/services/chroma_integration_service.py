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