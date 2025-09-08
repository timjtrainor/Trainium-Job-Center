"""Schemas for ChromaDB operations."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChromaUploadRequest(BaseModel):
    """Request schema for uploading data to ChromaDB."""
    
    collection_name: str = Field(..., description="Name of the ChromaDB collection")
    title: str = Field(..., description="Title for the document")
    tags: List[str] = Field(default_factory=list, description="Tags for the document")
    document_text: str = Field(..., description="The text content to upload")


class ChromaUploadResponse(BaseModel):
    """Response schema for ChromaDB upload operation."""
    
    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Status message")
    collection_name: str = Field(..., description="Name of the collection")
    document_id: str = Field(..., description="Generated document ID")
    chunks_created: int = Field(..., description="Number of text chunks created")


class ChromaCollectionInfo(BaseModel):
    """Information about a ChromaDB collection."""
    
    name: str = Field(..., description="Collection name")
    count: int = Field(..., description="Number of documents in collection")
    metadata: Optional[dict] = Field(None, description="Collection metadata")


class ChromaCollectionListResponse(BaseModel):
    """Response schema for listing ChromaDB collections."""
    
    collections: List[ChromaCollectionInfo] = Field(..., description="List of collections")