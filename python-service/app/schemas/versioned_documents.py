"""Schemas for versioned resume and proof point documents."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StatusTransition(BaseModel):
    """Represents a change in document status."""

    previous_status: Optional[str] = Field(None, alias="from", description="Previous status value")
    next_status: str = Field(..., alias="to", description="New status value")
    changed_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the transition")
    changed_by: Optional[str] = Field(
        default=None,
        description="Reviewer or system that triggered the transition"
    )
    notes: Optional[str] = Field(default=None, description="Additional context for the transition")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class ProofPointCreateRequest(BaseModel):
    """Request payload for creating or updating proof points."""

    profile_id: str = Field(..., description="Profile identifier for the proof point")
    role_title: str = Field(..., description="Role associated with the proof point")
    job_title: Optional[str] = Field(
        default=None,
        description="Specific job title or experience label for uniqueness",
    )
    location: Optional[str] = Field(
        default=None,
        description="Location associated with the proof point experience",
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date of the experience in ISO format",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date of the experience in ISO format",
    )
    is_current: Optional[bool] = Field(
        default=None,
        description="Whether the experience is currently ongoing",
    )
    company: str = Field(..., description="Company associated with the proof point")
    title: str = Field(..., description="Title for the proof point document")
    content: str = Field(..., description="Proof point content")
    status: str = Field("draft", description="Workflow status for the proof point")
    job_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata describing the job context"
    )
    impact_tags: List[str] = Field(default_factory=list, description="Tags describing impact areas")
    uploaded_at: Optional[datetime] = Field(
        default=None,
        description="Explicit upload timestamp override"
    )
    status_transitions: List[StatusTransition] = Field(
        default_factory=list,
        description="Historical status transitions"
    )
    additional_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata forwarded to the vector store"
    )

    def to_service_kwargs(self) -> Dict[str, Any]:
        """Convert the request into keyword arguments for the service layer."""

        transitions = [
            transition.model_dump(mode="json", by_alias=True) for transition in self.status_transitions
        ]

        return {
            "profile_id": self.profile_id,
            "role_title": self.role_title,
            "job_title": self.job_title,
            "location": self.location,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_current": self.is_current,
            "company": self.company,
            "content": self.content,
            "title": self.title,
            "job_metadata": self.job_metadata,
            "status": self.status,
            "impact_tags": self.impact_tags or None,
            "uploaded_at": self.uploaded_at,
            "status_transitions": transitions or None,
            "additional_metadata": self.additional_metadata or None,
        }


class ResumeCreateRequest(BaseModel):
    """Request payload for uploading resume versions."""

    profile_id: str = Field(..., description="Profile identifier for the resume")
    title: str = Field(..., description="Title for the resume document")
    content: str = Field(..., description="Resume content body")
    section: str = Field("resume", description="Section label for the resume")
    job_target: Optional[str] = Field(
        default=None,
        description="Job target or campaign identifier for versioning"
    )
    status: str = Field("draft", description="Workflow status for the resume")
    selected_proof_points: List[str] = Field(
        default_factory=list,
        description="Identifiers of proof points attached to this resume"
    )
    status_transitions: List[StatusTransition] = Field(
        default_factory=list,
        description="Historical status transitions"
    )
    approved_by: Optional[str] = Field(
        default=None,
        description="Reviewer approving the resume"
    )
    approved_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the resume was approved"
    )
    approval_notes: Optional[str] = Field(
        default=None,
        description="Reviewer notes captured during approval"
    )
    version: Optional[int] = Field(
        default=None,
        ge=1,
        description="Explicit version override for specialized workflows"
    )
    is_latest: Optional[bool] = Field(
        default=None,
        description="Force the resume to be treated as the latest version"
    )
    uploaded_at: Optional[datetime] = Field(
        default=None,
        description="Explicit upload timestamp override"
    )
    additional_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata forwarded to the vector store"
    )

    def to_service_kwargs(self) -> Dict[str, Any]:
        """Convert request payload to service parameters."""

        transitions = [
            transition.model_dump(mode="json", by_alias=True) for transition in self.status_transitions
        ]

        return {
            "title": self.title,
            "content": self.content,
            "profile_id": self.profile_id,
            "section": self.section,
            "uploaded_at": self.uploaded_at,
            "additional_metadata": self.additional_metadata or None,
            "job_target": self.job_target,
            "status": self.status,
            "selected_proof_points": self.selected_proof_points or None,
            "status_transitions": transitions or None,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "approval_notes": self.approval_notes,
            "version": self.version,
            "is_latest": self.is_latest,
        }


class ResumeUpdateRequest(BaseModel):
    """Partial update payload for resume metadata."""

    status: Optional[str] = Field(default=None, description="Updated workflow status")
    selected_proof_points: Optional[List[str]] = Field(
        default=None,
        description="Updated list of selected proof point identifiers"
    )
    approved_by: Optional[str] = Field(default=None, description="Reviewer approving the resume")
    approved_at: Optional[datetime] = Field(default=None, description="Approval timestamp")
    approval_notes: Optional[str] = Field(default=None, description="Reviewer notes")
    status_transitions: Optional[List[StatusTransition]] = Field(
        default=None,
        description="Explicit transition history replacement"
    )
    is_latest: Optional[bool] = Field(default=None, description="Mark this resume as the latest version")

    def to_service_kwargs(self) -> Dict[str, Any]:
        """Map populated fields to service keyword arguments."""

        payload = self.model_dump(exclude_unset=True)
        if "status_transitions" in payload:
            payload["status_transitions"] = [
                transition.model_dump(mode="json", by_alias=True)
                for transition in payload["status_transitions"] or []
            ]
        if "selected_proof_points" in payload and payload["selected_proof_points"] is not None:
            payload["selected_proof_points"] = list(payload["selected_proof_points"])
        return payload


class ResumeDocumentMetadata(BaseModel):
    """Metadata snapshot for a stored resume document."""

    profile_id: Optional[str] = Field(default=None)
    job_target: Optional[str] = Field(default=None)
    section: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    version: Optional[int] = Field(default=None)
    is_latest: Optional[bool] = Field(default=None)
    latest_version: Optional[bool] = Field(default=None)
    selected_proof_points: List[str] = Field(default_factory=list)
    status_transitions: List[StatusTransition] = Field(default_factory=list)
    approved_by: Optional[str] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    approval_notes: Optional[str] = Field(default=None)
    uploaded_at: Optional[datetime] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    timestamp: Optional[datetime] = Field(default=None)
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]) -> "ResumeDocumentMetadata":
        """Build a metadata model from raw Chroma metadata."""

        base_keys = {
            "profile_id",
            "job_target",
            "section",
            "title",
            "status",
            "version",
            "is_latest",
            "latest_version",
            "approved_by",
            "approved_at",
            "approval_notes",
            "uploaded_at",
            "created_at",
            "updated_at",
            "timestamp",
        }

        metadata: Dict[str, Any] = {key: raw.get(key) for key in base_keys}
        metadata["selected_proof_points"] = list(raw.get("selected_proof_points") or [])

        transitions = raw.get("status_transitions") or []
        metadata["status_transitions"] = [
            StatusTransition.model_validate(transition) for transition in transitions
        ]

        metadata["additional_metadata"] = {
            key: value
            for key, value in raw.items()
            if key not in base_keys
            and key not in {"status_transitions", "selected_proof_points"}
        }

        return cls(**metadata)


class ResumeDocumentResponse(BaseModel):
    """Standard response payload for resume metadata updates."""

    document_id: str = Field(..., description="Identifier of the updated resume document")
    metadata: ResumeDocumentMetadata = Field(..., description="Metadata snapshot after the update")
    message: Optional[str] = Field(default=None, description="Optional status message")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")
