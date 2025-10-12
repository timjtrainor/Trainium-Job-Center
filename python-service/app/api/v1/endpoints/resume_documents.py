"""FastAPI endpoints for managing resumes and proof points."""

from fastapi import APIRouter, Depends

from ....schemas.responses import StandardResponse, create_error_response, create_success_response
from ....schemas.versioned_documents import (
    ProofPointCreateRequest,
    ResumeCreateRequest,
    ResumeDocumentMetadata,
    ResumeDocumentResponse,
    ResumeUpdateRequest,
)
from ....services.chroma_integration_service import ChromaIntegrationService


router = APIRouter()


def get_chroma_integration_service() -> ChromaIntegrationService:
    """Factory dependency for the integration service."""

    return ChromaIntegrationService()


@router.post("/proof-points", response_model=StandardResponse, summary="Create a proof point")
async def create_proof_point(
    payload: ProofPointCreateRequest,
    service: ChromaIntegrationService = Depends(get_chroma_integration_service),
) -> StandardResponse:
    """Persist a proof point document with version-aware metadata."""

    result = await service.create_proof_point_for_job(**payload.to_service_kwargs())

    if not result.success:
        return create_error_response(
            error="Failed to create proof point",
            message=result.message,
            data={
                "collection": result.collection_name,
                "document_id": result.document_id or None,
            },
        )

    return create_success_response(data=result.model_dump())


@router.post("/resumes", response_model=StandardResponse, summary="Upload a resume version")
async def upload_resume(
    payload: ResumeCreateRequest,
    service: ChromaIntegrationService = Depends(get_chroma_integration_service),
) -> StandardResponse:
    """Upload a resume document and manage its metadata."""

    result = await service.add_resume_document(**payload.to_service_kwargs())

    if not result.success:
        return create_error_response(
            error="Failed to upload resume",
            message=result.message,
            data={
                "collection": result.collection_name,
                "document_id": result.document_id or None,
            },
        )

    return create_success_response(data=result.model_dump())


@router.patch("/resumes/{document_id}", response_model=StandardResponse, summary="Update resume metadata")
async def update_resume(
    document_id: str,
    payload: ResumeUpdateRequest,
    service: ChromaIntegrationService = Depends(get_chroma_integration_service),
) -> StandardResponse:
    """Update metadata for an existing resume document."""

    update_kwargs = payload.to_service_kwargs()

    if not update_kwargs:
        return create_error_response(
            error="No updates provided",
            message="Submit at least one field to update.",
            data={"document_id": document_id},
        )

    result = await service.update_resume_document(document_id=document_id, **update_kwargs)

    if not result.get("success"):
        return create_error_response(
            error="Failed to update resume",
            message=result.get("message"),
            data={"document_id": document_id},
        )

    metadata = ResumeDocumentMetadata.from_raw(result.get("metadata", {}))

    response = ResumeDocumentResponse(
        document_id=document_id,
        metadata=metadata,
        message=result.get("message"),
    )

    return create_success_response(data=response.model_dump(by_alias=True))
