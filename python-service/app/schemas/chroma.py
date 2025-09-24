"""Schemas for ChromaDB operations."""

from typing import Dict, List, Optional, Any
from datetime import datetime
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


# Career-related upload schemas with enforced section and uploaded_at fields
class CareerBrandUpload(BaseModel):
    """Schema for uploading career brand documents to ChromaDB.
    
    Metadata Schema:
    - profile_id: str (required) - User profile identifier
    - section: str (required) - Document section/category
    - uploaded_at: datetime (auto) - Upload timestamp
    - source: str (optional) - Document source
    - author: str (optional) - Document author
    """
    title: str = Field(..., description="Title of the career brand document")
    content: str = Field(..., description="Content of the career brand document")
    profile_id: str = Field(..., description="User profile identifier")
    section: str = Field(..., description="Document section/category")
    source: str = Field("", description="Document source")
    author: str = Field("", description="Document author")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional optional metadata")


class CareerPathsUpload(BaseModel):
    """Schema for uploading career path documents to ChromaDB.
    
    Metadata Schema:
    - profile_id: str (required) - User profile identifier
    - section: str (required) - Document section/category
    - uploaded_at: datetime (auto) - Upload timestamp
    - source: str (optional) - Document source
    - author: str (optional) - Document author
    """
    title: str = Field(..., description="Title of the career path document")
    content: str = Field(..., description="Content of the career path document")
    profile_id: str = Field(..., description="User profile identifier")
    section: str = Field(..., description="Document section/category")
    source: str = Field("", description="Document source")
    author: str = Field("", description="Document author")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional optional metadata")


class JobSearchStrategiesUpload(BaseModel):
    """Schema for uploading job search strategy documents to ChromaDB.
    
    Metadata Schema:
    - profile_id: str (required) - User profile identifier
    - section: str (required) - Document section/category
    - uploaded_at: datetime (auto) - Upload timestamp
    - source: str (optional) - Document source
    - author: str (optional) - Document author
    """
    title: str = Field(..., description="Title of the job search strategy document")
    content: str = Field(..., description="Content of the job search strategy document")
    profile_id: str = Field(..., description="User profile identifier")
    section: str = Field(..., description="Document section/category")
    source: str = Field("", description="Document source")
    author: str = Field("", description="Document author")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional optional metadata")


class ResumeUpload(BaseModel):
    """Schema for uploading resume documents to ChromaDB.
    
    Metadata Schema:
    - profile_id: str (required) - User profile identifier
    - section: str (default: "resume") - Document section/category
    - uploaded_at: datetime (auto) - Upload timestamp
    - title: str (required) - Resume title
    """
    title: str = Field(..., description="Title of the resume")
    content: str = Field(..., description="Content of the resume")
    profile_id: str = Field(..., description="User profile identifier")
    section: str = Field("resume", description="Document section/category")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional optional metadata")


# Job posting and company profile schemas with enforced standard metadata
class JobPostingUpload(BaseModel):
    """Schema for uploading job postings to ChromaDB.
    
    Standard Metadata Fields (enforced programmatically):
    - job_id: str (required) - Unique job identifier
    - source: str (required) - Job posting source
    - status: str (required) - Job posting status
    - uploaded_at: datetime (auto) - Upload timestamp
    """
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    location: str = Field("", description="Job location")
    salary_range: str = Field("", description="Salary range")
    skills: List[str] = Field(default_factory=list, description="Required skills")
    job_type: str = Field("", description="Job type (full-time, part-time, etc.)")
    experience_level: str = Field("", description="Required experience level")
    # Standard fields that will be enforced programmatically
    job_id: str = Field(..., description="Unique job identifier")
    source: str = Field(..., description="Job posting source")
    status: str = Field("active", description="Job posting status")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional flexible metadata")


class CompanyProfileUpload(BaseModel):
    """Schema for uploading company profiles to ChromaDB.
    
    Standard Metadata Fields (enforced programmatically):
    - company_id: str (required) - Unique company identifier
    - industry: str (required) - Company industry
    - company_stage: str (required) - Company stage (startup, growth, enterprise, etc.)
    - ai_first: bool (required) - Whether company is AI-first
    - uploaded_at: datetime (auto) - Upload timestamp
    """
    company_name: str = Field(..., description="Company name")
    description: str = Field(..., description="Company description")
    industry: str = Field(..., description="Company industry")
    size: str = Field("", description="Company size")
    culture_info: str = Field("", description="Company culture information")
    benefits: List[str] = Field(default_factory=list, description="Company benefits")
    values: List[str] = Field(default_factory=list, description="Company values")
    # Standard fields that will be enforced programmatically
    company_id: str = Field(..., description="Unique company identifier")
    company_stage: str = Field(..., description="Company stage (startup, growth, enterprise, etc.)")
    ai_first: bool = Field(False, description="Whether company is AI-first")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional flexible metadata")