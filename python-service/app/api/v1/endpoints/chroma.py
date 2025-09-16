"""ChromaDB management endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from loguru import logger
import json

from ....schemas.chroma import (
    ChromaUploadRequest, 
    ChromaUploadResponse, 
    ChromaCollectionListResponse,
    ChromaCollectionInfo
)
from ....services.chroma_service import ChromaService
from ....schemas.responses import create_success_response, create_error_response


router = APIRouter()


def get_chroma_service() -> ChromaService:
    """Dependency to get ChromaService instance."""
    return ChromaService()


@router.post("/chroma/upload", response_model=ChromaUploadResponse)
async def upload_to_chroma(
    collection_name: str = Form(..., description="Name of the ChromaDB collection"),
    title: str = Form(..., description="Title for the document"),
    tags: str = Form(default="", description="Comma-separated tags"),
    file: UploadFile = File(..., description="Text file to upload"),
    metadata: str = Form(default="{}", description="JSON string of additional metadata"),
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """
    Upload a text file to ChromaDB with user-defined metadata.
    
    - **collection_name**: Name for the ChromaDB collection
    - **title**: Title for the document
    - **tags**: Comma-separated list of tags
    - **file**: Text file to upload (.txt, .md, etc.)
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith(('.txt', '.md', '.text')):
            raise HTTPException(
                status_code=400, 
                detail="Only text files (.txt, .md, .text) are supported"
            )
        
        # Read file content
        try:
            content = await file.read()
            document_text = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File must be valid UTF-8 encoded text"
            )
        
        if not document_text.strip():
            raise HTTPException(
                status_code=400,
                detail="File appears to be empty"
            )
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []

        # Parse metadata
        try:
            metadata_dict = json.loads(metadata) if metadata else {}
            if not isinstance(metadata_dict, dict):
                raise ValueError("Metadata must be a JSON object")
        except (json.JSONDecodeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Metadata must be a valid JSON object",
            )

        # Create request object
        request = ChromaUploadRequest(
            collection_name=collection_name,
            title=title,
            tags=tag_list,
            document_text=document_text,
            metadata=metadata_dict,
        )
        
        # Initialize service if needed
        await chroma_service.initialize()
        
        # Upload to ChromaDB
        result = await chroma_service.upload_document(request)
        
        if result.success:
            logger.info(
                f"Successfully uploaded file '{file.filename}' to collection '{collection_name}'"
            )
        else:
            # Log the detailed error for debugging
            logger.error(
                f"Failed to upload file '{file.filename}' to collection '{collection_name}': "
                f"{result.message}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chroma upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/chroma/upload-text", response_model=ChromaUploadResponse)
async def upload_text_to_chroma(
    request: ChromaUploadRequest,
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """
    Upload text directly to ChromaDB with user-defined metadata.
    
    Alternative endpoint for uploading text content without file upload.
    """
    try:
        if not request.document_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Document text cannot be empty"
            )
        
        # Initialize service if needed
        await chroma_service.initialize()
        
        # Upload to ChromaDB
        result = await chroma_service.upload_document(request)
        
        if result.success:
            logger.info(
                f"Successfully uploaded text to collection '{request.collection_name}'"
            )
        else:
            # Log the detailed error for debugging
            logger.error(
                f"Failed to upload text to collection '{request.collection_name}': "
                f"{result.message}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chroma text upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/chroma/collections", response_model=ChromaCollectionListResponse)
async def list_chroma_collections(
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """List all ChromaDB collections with their metadata."""
    try:
        # Initialize service if needed
        await chroma_service.initialize()
        
        collections = await chroma_service.list_collections()
        
        return ChromaCollectionListResponse(collections=collections)
        
    except Exception as e:
        logger.error(f"Failed to list ChromaDB collections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.delete("/chroma/collections/{collection_name}")
async def delete_chroma_collection(
    collection_name: str,
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """Delete a ChromaDB collection."""
    try:
        # Initialize service if needed
        await chroma_service.initialize()
        
        success = await chroma_service.delete_collection(collection_name)
        
        if success:
            return create_success_response(
                message=f"Successfully deleted collection '{collection_name}'"
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to delete collection '{collection_name}'"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete collection '{collection_name}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete collection: {str(e)}"
        )


@router.get("/chroma/collections/{collection_name}/documents")
async def list_collection_documents(
    collection_name: str,
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """List all documents in a ChromaDB collection."""
    try:
        # Initialize service if needed
        await chroma_service.initialize()
        
        documents = await chroma_service.list_documents(collection_name)
        
        return {"documents": documents}
        
    except Exception as e:
        logger.error(f"Failed to list documents in collection '{collection_name}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/chroma/collections/{collection_name}/documents/{document_id}")
async def delete_collection_document(
    collection_name: str,
    document_id: str,
    chroma_service: ChromaService = Depends(get_chroma_service)
):
    """Delete a specific document from a ChromaDB collection."""
    try:
        # Initialize service if needed
        await chroma_service.initialize()
        
        success = await chroma_service.delete_document(collection_name, document_id)
        
        if success:
            return create_success_response(
                message=f"Successfully deleted document '{document_id}' from collection '{collection_name}'"
            )
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Document '{document_id}' not found in collection '{collection_name}'"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document '{document_id}' from collection '{collection_name}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete document: {str(e)}"
        )