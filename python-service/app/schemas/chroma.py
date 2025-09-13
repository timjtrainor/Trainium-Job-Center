"""Schemas for ChromaDB operations."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ChromaUploadRequest(BaseModel):
    """Request schema for uploading data to ChromaDB."""

    collection_name: str = Field(..., description="Name of the ChromaDB collection")
    title: str = Field(..., description="Title for the document")
    tags: List[str] = Field(default_factory=list, description="Tags for the document")
    document_text: str = Field(..., description="The text content to upload")
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional metadata to include with each chunk",
    )


class ChromaUploadResponse(BaseModel):
    """Response schema for ChromaDB upload operation."""
    
    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Status message or detailed error information")
    collection_name: str = Field(..., description="Name of the collection")
    document_id: str = Field(..., description="Generated document ID")
    chunks_created: int = Field(..., description="Number of text chunks created")
    error_type: Optional[str] = Field(None, description="Type of error if upload failed")
    suggestions: Optional[List[str]] = Field(None, description="Suggested actions to resolve errors")


class ChromaCollectionInfo(BaseModel):
    """Information about a ChromaDB collection."""
    
    name: str = Field(..., description="Collection name")
    count: int = Field(..., description="Number of documents in collection")
    metadata: Optional[dict] = Field(None, description="Collection metadata")


class ChromaCollectionListResponse(BaseModel):
    """Response schema for listing ChromaDB collections."""
    
    collections: List[ChromaCollectionInfo] = Field(..., description="List of collections")