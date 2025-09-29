"""Career brand document upload and management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from loguru import logger

from ....services.career_brand_service import get_career_brand_service, CareerBrandService
from ....schemas.career_brand import (
    CareerBrandUploadRequest,
    CareerBrandUploadResponse,
    CareerBrandDocumentInfo
)

router = APIRouter(tags=["Career Brand"])


@router.post("/documents/career-brand", response_model=CareerBrandUploadResponse)
async def upload_career_brand_document(
    request: CareerBrandUploadRequest,
    service: CareerBrandService = Depends(get_career_brand_service)
):
    """
    Upload a career brand document with automatic versioning.

    This endpoint integrates with ChromaUploadView and ensures:
    - Only one "latest" version exists per section/narrative combination
    - Previous versions are preserved but marked as not latest
    - CrewAI knowledge sources can filter for latest_version=true

    The uploaded document becomes immediately available to CrewAI agents
    for knowledge-based job posting analysis.
    """
    try:
        # Validate required content
        if not request.content.strip():
            raise HTTPException(
                status_code=400,
                detail="Document content cannot be empty"
            )

        if not request.title.strip():
            raise HTTPException(
                status_code=400,
                detail="Document title cannot be empty"
            )

        # Initialize service if needed
        await service.initialize()

        # Upload with versioning
        result = await service.upload_career_brand_document(request)

        if result.success:
            logger.info(
                f"Successfully uploaded career brand document: {request.section} "
                f"v{result.version} for narrative {request.profile_id}"
            )
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail=result.message
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading career brand document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/documents/career-path", response_model=CareerBrandUploadResponse)
async def upload_career_path_document(
    request: CareerBrandUploadRequest,
    service: CareerBrandService = Depends(get_career_brand_service)
):
    """
    Upload a career path document (reuses career brand versioning logic).

    Career paths are stored separately but use similar versioning logic.
    """
    try:
        # This would map to a different section type or collection
        # For now, we'll handle it through the same service
        await service.initialize()
        result = await service.upload_career_brand_document(request)

        if result.success:
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail=result.message
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading career path document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/documents/job-search-strategies", response_model=CareerBrandUploadResponse)
async def upload_job_search_strategy_document(
    request: CareerBrandUploadRequest,
    service: CareerBrandService = Depends(get_career_brand_service)
):
    """
    Upload a job search strategy document (reuses career brand versioning logic).
    """
    try:
        await service.initialize()
        result = await service.upload_career_brand_document(request)

        if result.success:
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail=result.message
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading job search strategy document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/documents/career-brand/{narrative_id}", response_model=List[CareerBrandDocumentInfo])
async def list_career_brand_documents(
    narrative_id: str,
    show_history: bool = Query(False, description="Whether to show full version history or just latest versions"),
    service: CareerBrandService = Depends(get_career_brand_service)
):
    """
    List career brand documents for a narrative.

    By default returns only the latest version of each section.
    When show_history=true, returns all versions for audit/review purposes.
    """
    try:
        await service.initialize()
        documents = await service.get_career_brand_documents(
            narrative_id=narrative_id,
            show_history=show_history
        )

        logger.info(f"Retrieved {len(documents)} career brand documents for narrative {narrative_id}")
        return documents

    except Exception as e:
        logger.error(f"Failed to list career brand documents for narrative {narrative_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.delete("/documents/career-brand/{document_id}")
async def delete_career_brand_document(
    document_id: str,
    narrative_id: str = Query(..., description="Narrative ID to verify ownership"),
    service: CareerBrandService = Depends(get_career_brand_service)
):
    """
    Delete a career brand document.

    Note: This permanently removes the document. For most cases,
    prefer uploading new versions which automatically mark old versions as not latest.
    """
    try:
        await service.initialize()

        success = await service.delete_career_brand_document(document_id, narrative_id)

        if success:
            logger.info(f"Successfully deleted career brand document {document_id}")
            return {
                "success": True,
                "message": f"Document {document_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found or could not be deleted"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete career brand document {document_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/documents", response_model=List[CareerBrandDocumentInfo])
async def get_uploaded_documents(
    profile_id: str = Query(..., description="Profile ID (narrative ID) for filtering documents"),
    show_history: bool = Query(False, description="Whether to show full version history"),
    service: CareerBrandService = Depends(get_career_brand_service)
):
    """
    Get uploaded documents for a profile/narrative (matches frontend expectations).

    This endpoint matches the frontend's expected URL pattern:
    GET /api/documents?profile_id={profile_id}

    Maps profile_id (frontend term) to narrative_id (backend term) for compatibility.
    """
    try:
        await service.initialize()
        documents = await service.get_career_brand_documents(
            narrative_id=profile_id,  # Map profile_id to narrative_id
            show_history=show_history
        )

        logger.info(f"Retrieved {len(documents)} documents for profile {profile_id}")
        return documents

    except Exception as e:
        logger.error(f"Failed to get documents for profile {profile_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve documents: {str(e)}"
        )
