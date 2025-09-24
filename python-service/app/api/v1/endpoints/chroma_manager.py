"""API endpoints for ChromaDB manager functionality."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ....services.chroma_integration_service import get_chroma_integration_service
from ....services.chroma_manager import get_chroma_manager, CollectionType
from ....schemas.chroma import (
    ChromaUploadResponse, 
    CareerBrandUpload, 
    CareerPathsUpload, 
    JobSearchStrategiesUpload,
    ResumeUpload,
    JobPostingUpload,
    CompanyProfileUpload
)


router = APIRouter(prefix="/chroma-manager", tags=["ChromaDB Manager"])


class SearchRequest(BaseModel):
    """Schema for searching ChromaDB collections."""
    query: str
    collections: Optional[List[str]] = None
    n_results: int = 5
    profile_id: Optional[str] = None  # Add profile_id filtering
    section: Optional[str] = None     # Add section filtering


class BulkJobPostingUpload(BaseModel):
    """Schema for bulk uploading job postings."""
    job_postings: List[JobPostingUpload]


@router.get("/status")
async def get_chroma_status():
    """Get the status of ChromaDB collections and configurations."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()
        status = await service.get_collection_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ChromaDB status: {str(e)}")


@router.get("/collections")
async def list_collections():
    """List all available ChromaDB collections."""
    try:
        manager = get_chroma_manager()
        await manager.initialize()
        collections = await manager.list_all_collections()
        
        return {
            "collections": [
                {
                    "name": col.name,
                    "count": col.count,
                    "metadata": col.metadata
                }
                for col in collections
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.get("/collection-types")
async def list_collection_types():
    """List all registered collection types and their configurations."""
    try:
        manager = get_chroma_manager()
        configs = manager.list_registered_collections()
        
        return {
            "collection_types": [
                {
                    "name": config.name,
                    "type": config.collection_type.value,
                    "description": config.description,
                    "chunk_size": config.chunk_size,
                    "chunk_overlap": config.chunk_overlap,
                    "metadata_schema": config.metadata_schema
                }
                for config in configs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list collection types: {str(e)}")


@router.post("/job-posting", response_model=ChromaUploadResponse)
async def upload_job_posting(job_posting: JobPostingUpload, background_tasks: BackgroundTasks):
    """Upload a job posting to the job_postings collection."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()
        
        # Enforce standard metadata fields programmatically
        standard_metadata = {
            "job_id": job_posting.job_id,
            "source": job_posting.source,
            "status": job_posting.status,
            "uploaded_at": job_posting.uploaded_at.isoformat()
        }
        
        # Merge with additional metadata
        final_metadata = {**standard_metadata, **job_posting.metadata}
        
        result = await service.add_job_posting(
            title=job_posting.title,
            company=job_posting.company,
            description=job_posting.description,
            location=job_posting.location,
            salary_range=job_posting.salary_range,
            skills=job_posting.skills,
            job_type=job_posting.job_type,
            experience_level=job_posting.experience_level,
            additional_metadata=final_metadata
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload job posting: {str(e)}")


@router.post("/company-profile", response_model=ChromaUploadResponse)
async def upload_company_profile(company_profile: CompanyProfileUpload):
    """Upload a company profile to the company_profiles collection."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()
        
        # Enforce standard metadata fields programmatically
        standard_metadata = {
            "company_id": company_profile.company_id,
            "industry": company_profile.industry,
            "company_stage": company_profile.company_stage,
            "ai_first": company_profile.ai_first,
            "uploaded_at": company_profile.uploaded_at.isoformat()
        }
        
        # Merge with additional metadata
        final_metadata = {**standard_metadata, **company_profile.metadata}
        
        result = await service.add_company_profile(
            company_name=company_profile.company_name,
            description=company_profile.description,
            industry=company_profile.industry,
            size=company_profile.size,
            culture_info=company_profile.culture_info,
            benefits=company_profile.benefits,
            values=company_profile.values,
            additional_metadata=final_metadata
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload company profile: {str(e)}")


@router.post("/career-brand", response_model=ChromaUploadResponse)
async def upload_career_brand(career_brand: CareerBrandUpload):
    """Upload a career brand document to the career_brand collection."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()
        
        result = await service.add_career_brand_document(
            title=career_brand.title,
            content=career_brand.content,
            profile_id=career_brand.profile_id,
            source=career_brand.source,
            author=career_brand.author,
            section=career_brand.section,
            uploaded_at=career_brand.uploaded_at,
            additional_metadata=career_brand.metadata
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload career brand document: {str(e)}")


@router.post("/career-paths", response_model=ChromaUploadResponse)
async def upload_career_paths(career_paths: CareerPathsUpload):
    """Upload a career path document to the career_paths collection."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()

        result = await service.add_career_path_document(
            title=career_paths.title,
            content=career_paths.content,
            profile_id=career_paths.profile_id,
            source=career_paths.source,
            author=career_paths.author,
            section=career_paths.section,
            uploaded_at=career_paths.uploaded_at,
            additional_metadata=career_paths.metadata
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload career path document: {str(e)}")


@router.post("/job-search-strategies", response_model=ChromaUploadResponse)
async def upload_job_search_strategies(job_search_strategies: JobSearchStrategiesUpload):
    """Upload a job search strategy document to the job_search_strategies collection."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()

        result = await service.add_job_search_strategies_document(
            title=job_search_strategies.title,
            content=job_search_strategies.content,
            profile_id=job_search_strategies.profile_id,
            source=job_search_strategies.source,
            author=job_search_strategies.author,
            section=job_search_strategies.section,
            uploaded_at=job_search_strategies.uploaded_at,
            additional_metadata=job_search_strategies.metadata
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload job search strategy document: {str(e)}")


@router.post("/resume", response_model=ChromaUploadResponse)
async def upload_resume(resume: ResumeUpload):
    """Upload a resume document to the resumes collection."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()

        result = await service.add_resume_document(
            title=resume.title,
            content=resume.content,
            profile_id=resume.profile_id,
            section=resume.section,
            uploaded_at=resume.uploaded_at,
            additional_metadata=resume.metadata
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload resume document: {str(e)}")

@router.post("/bulk-job-postings")
async def bulk_upload_job_postings(bulk_request: BulkJobPostingUpload, background_tasks: BackgroundTasks):
    """Bulk upload multiple job postings."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()
        
        # Convert Pydantic models to dicts
        job_postings_data = []
        for job_posting in bulk_request.job_postings:
            job_postings_data.append(job_posting.dict())
        
        # Execute bulk upload in background
        def run_bulk_upload():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(
                    service.bulk_upload_job_postings(job_postings_data)
                )
                return results
            finally:
                loop.close()
        
        background_tasks.add_task(run_bulk_upload)
        
        return {
            "message": f"Bulk upload of {len(bulk_request.job_postings)} job postings started",
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start bulk upload: {str(e)}")


@router.post("/search")
async def search_collections(search_request: SearchRequest):
    """Search across ChromaDB collections with optional profile_id and section filtering."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()
        
        context = await service.search_for_crew_context(
            query=search_request.query,
            collections=search_request.collections,
            n_results=search_request.n_results,
            profile_id=search_request.profile_id,
            section=search_request.section
        )
        
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search collections: {str(e)}")


@router.post("/prepare-rag-context")
async def prepare_rag_context(
    job_posting: Dict[str, Any],
    profile_id: Optional[str] = None,
    section: Optional[str] = None,
    additional_queries: Optional[List[str]] = None
):
    """Prepare comprehensive RAG context for CrewAI job posting analysis with profile_id and section filtering."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()
        
        context = await service.prepare_crew_rag_context(
            job_posting=job_posting,
            profile_id=profile_id,
            section=section,
            additional_queries=additional_queries or []
        )
        
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prepare RAG context: {str(e)}")


@router.delete("/collection/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a ChromaDB collection."""
    try:
        manager = get_chroma_manager()
        await manager.initialize()
        
        success = await manager.delete_collection(collection_name)
        
        if success:
            return {"message": f"Collection '{collection_name}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found or could not be deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete collection: {str(e)}")


@router.post("/initialize")
async def initialize_chroma():
    """Initialize ChromaDB with default collections."""
    try:
        service = get_chroma_integration_service()
        await service.initialize()
        
        return {"message": "ChromaDB initialized successfully with default collections"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize ChromaDB: {str(e)}")