"""Schemas for career brand service operations."""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class CareerBrandUploadRequest(BaseModel):
    """Request schema for uploading career brand documents."""

    profile_id: str = Field(..., description="Narrative/profile ID that owns this document")
    section: str = Field(..., description="Career brand section (e.g., 'North Star', 'Values', etc.)")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Full document content text")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class CareerBrandUploadResponse(BaseModel):
    """Response schema for career brand document uploads."""

    success: bool = Field(..., description="Whether the upload was successful")
    message: str = Field(..., description="Response message or error description")
    document_id: str = Field(default="", description="Unique document identifier")
    section: str = Field(..., description="Career brand section")
    version: int = Field(default=1, description="Document version number")
    latest_version: bool = Field(default=True, description="Whether this is the latest version")
    narrative_id: str = Field(default="", description="Narrative/profile ID")
    uploaded_at: str = Field(default="", description="Upload timestamp in ISO format")


class CareerBrandDocumentInfo(BaseModel):
    """Information about a career brand document."""

    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    section: str = Field(..., description="Career brand section")
    latest_version: bool = Field(default=True, description="Whether this is the latest version")
    version: int = Field(default=1, description="Document version number")
    created_at: str = Field(..., description="Creation timestamp")
    content_preview: str = Field(..., description="Content preview (first 200 chars)")
    narrative_id: str = Field(..., description="Narrative/profile ID that owns this document")


class CareerBrandVersionHistory(BaseModel):
    """Version history for a career brand section."""

    section: str = Field(..., description="Career brand section")
    narrative_id: str = Field(..., description="Narrative/profile ID")
    versions: List[CareerBrandDocumentInfo] = Field(default_factory=list, description="All versions ordered by recency")
    total_versions: int = Field(default=0, description="Total number of versions")
    latest_version: Optional[CareerBrandDocumentInfo] = Field(None, description="Latest version information")


class CareerBrandSectionMapping(BaseModel):
    """Mapping between user-friendly section names and system section names."""

    user_friendly_name: str = Field(..., description="Name shown to users")
    system_name: str = Field(..., description="Internal system section name")
    description: str = Field(..., description="Description of what this section contains")
    agent_responsibility: str = Field(..., description="Which CrewAI agent handles this section")

    @classmethod
    def get_all_mappings(cls) -> List['CareerBrandSectionMapping']:
        """Get all standard career brand section mappings."""
        return [
            CareerBrandSectionMapping(
                user_friendly_name="North Star",
                system_name="north_star_vision",
                description="Long-term vision and purpose for career",
                agent_responsibility="north_star_matcher"
            ),
            CareerBrandSectionMapping(
                user_friendly_name="Values",
                system_name="values_compass",
                description="Core values and work style preferences",
                agent_responsibility="values_compass_matcher"
            ),
            CareerBrandSectionMapping(
                user_friendly_name="Positioning Statement",
                system_name="values_compass",
                description="Professional positioning and value proposition",
                agent_responsibility="values_compass_matcher"
            ),
            CareerBrandSectionMapping(
                user_friendly_name="Impact Story",
                system_name="values_compass",
                description="Measurable impact and achievements",
                agent_responsibility="values_compass_matcher"
            ),
            CareerBrandSectionMapping(
                user_friendly_name="Signature Capability",
                system_name="trajectory_mastery",
                description="Unique skills and capabilities",
                agent_responsibility="trajectory_mastery_matcher"
            )
        ]
