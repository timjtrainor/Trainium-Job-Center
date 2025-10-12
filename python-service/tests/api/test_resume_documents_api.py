"""API tests for resume and proof point management endpoints."""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Tuple

import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/testdb")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.resume_documents import (
    get_chroma_integration_service,
    router as resume_router,
)
from app.schemas.chroma import ChromaUploadResponse


class FakeChromaIntegrationService:
    """In-memory stand-in for the Chroma integration service."""

    def __init__(self) -> None:
        self.proof_points: Dict[str, Dict[str, Any]] = {}
        self.resumes: Dict[str, Dict[str, Any]] = {}
        self.resume_index: Dict[Tuple[Optional[str], Optional[str]], List[str]] = {}
        self.counter = 0

    async def create_proof_point_for_job(
        self,
        profile_id: str,
        role_title: str,
        company: str,
        content: str,
        title: str,
        *,
        job_metadata: Optional[Dict[str, Any]] = None,
        status: str = "draft",
        impact_tags: Optional[List[str]] = None,
        uploaded_at: Optional[datetime] = None,
        status_transitions: Optional[List[Dict[str, Any]]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> ChromaUploadResponse:
        doc_id = f"proof-{len(self.proof_points) + 1}"
        self.proof_points[doc_id] = {
            "profile_id": profile_id,
            "role_title": role_title,
            "company": company,
            "content": content,
            "title": title,
            "status": status,
            "job_metadata": job_metadata or {},
            "impact_tags": list(impact_tags or []),
            "uploaded_at": self._normalize_datetime(uploaded_at),
            "status_transitions": [
                self._normalize_transition(transition)
                for transition in (status_transitions or [])
            ],
            "additional_metadata": additional_metadata or {},
        }
        return ChromaUploadResponse(
            success=True,
            message="Proof point created",
            collection_name="proof_points",
            document_id=doc_id,
            chunks_created=1,
        )

    async def add_resume_document(
        self,
        title: str,
        content: str,
        profile_id: str,
        section: str = "resume",
        uploaded_at: Optional[datetime] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
        *,
        job_target: Optional[str] = None,
        status: Optional[str] = None,
        selected_proof_points: Optional[List[str]] = None,
        status_transitions: Optional[List[Dict[str, Any]]] = None,
        approved_by: Optional[str] = None,
        approved_at: Optional[datetime] = None,
        approval_notes: Optional[str] = None,
        version: Optional[int] = None,
        is_latest: Optional[bool] = None,
    ) -> ChromaUploadResponse:
        self.counter += 1
        document_id = f"resume-{self.counter}"
        key = (profile_id, job_target)
        now_iso = self._normalize_datetime(uploaded_at) or datetime.now(UTC).isoformat()

        transitions = [
            self._normalize_transition(transition)
            for transition in (status_transitions or [])
        ]

        current_version = version or (len(self.resume_index.get(key, [])) + 1)
        latest_flag = True if is_latest is None else bool(is_latest)

        metadata = {
            "profile_id": profile_id,
            "job_target": job_target,
            "section": section,
            "title": title,
            "status": status or "draft",
            "selected_proof_points": list(selected_proof_points or []),
            "status_transitions": transitions,
            "approved_by": approved_by,
            "approved_at": self._normalize_datetime(approved_at),
            "approval_notes": approval_notes,
            "version": current_version,
            "is_latest": latest_flag,
            "latest_version": latest_flag,
            "uploaded_at": now_iso,
            "created_at": now_iso,
            "updated_at": now_iso,
            "timestamp": now_iso,
            "additional_metadata": additional_metadata or {},
        }

        if latest_flag:
            for existing_id in self.resume_index.get(key, []):
                existing_meta = self.resumes[existing_id]["metadata"]
                existing_meta["is_latest"] = False
                existing_meta["latest_version"] = False
                existing_meta["updated_at"] = now_iso

        self.resumes[document_id] = {
            "content": content,
            "metadata": metadata,
        }
        self.resume_index.setdefault(key, []).append(document_id)

        return ChromaUploadResponse(
            success=True,
            message="Resume uploaded",
            collection_name="resumes",
            document_id=document_id,
            chunks_created=1,
        )

    async def update_resume_document(
        self,
        document_id: str,
        *,
        status: Optional[str] = None,
        selected_proof_points: Optional[List[str]] = None,
        approved_by: Optional[str] = None,
        approved_at: Optional[datetime] = None,
        approval_notes: Optional[str] = None,
        status_transitions: Optional[List[Dict[str, Any]]] = None,
        is_latest: Optional[bool] = None,
    ) -> Dict[str, Any]:
        if document_id not in self.resumes:
            return {
                "success": False,
                "message": "Resume not found",
                "document_id": document_id,
            }

        metadata = dict(self.resumes[document_id]["metadata"])
        now_iso = datetime.now(UTC).isoformat()
        previous_status = metadata.get("status")

        if status is not None:
            metadata["status"] = status
            if status != previous_status:
                transitions = list(metadata.get("status_transitions") or [])
                transitions.append(
                    {
                        "from": previous_status,
                        "to": status,
                        "changed_at": now_iso,
                        "changed_by": approved_by or metadata.get("approved_by"),
                    }
                )
                metadata["status_transitions"] = transitions

        if status_transitions is not None:
            metadata["status_transitions"] = [
                self._normalize_transition(transition)
                for transition in status_transitions
            ]

        if selected_proof_points is not None:
            metadata["selected_proof_points"] = list(selected_proof_points)

        if approved_by is not None:
            metadata["approved_by"] = approved_by

        if approved_at is not None:
            metadata["approved_at"] = self._normalize_datetime(approved_at)

        if approval_notes is not None:
            metadata["approval_notes"] = approval_notes

        if is_latest is not None:
            metadata["is_latest"] = is_latest
            metadata["latest_version"] = is_latest

        metadata["updated_at"] = now_iso

        self.resumes[document_id]["metadata"] = metadata

        if metadata.get("is_latest"):
            key = (metadata.get("profile_id"), metadata.get("job_target"))
            for other_id in self.resume_index.get(key, []):
                if other_id == document_id:
                    continue
                other_meta = self.resumes[other_id]["metadata"]
                other_meta["is_latest"] = False
                other_meta["latest_version"] = False
                other_meta["updated_at"] = now_iso

        return {
            "success": True,
            "message": "Resume metadata updated",
            "document_id": document_id,
            "metadata": metadata,
        }

    def _normalize_datetime(self, value: Optional[Any]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.isoformat()

    def _normalize_transition(self, transition: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(transition)
        changed_at = normalized.get("changed_at")
        normalized["changed_at"] = (
            self._normalize_datetime(changed_at) or datetime.now(UTC).isoformat()
        )
        return normalized


@pytest.fixture()
def api_client() -> Tuple[TestClient, FakeChromaIntegrationService]:
    """Create an API client with a fake service dependency."""

    app = FastAPI()
    service = FakeChromaIntegrationService()
    app.include_router(resume_router)
    app.dependency_overrides[get_chroma_integration_service] = lambda: service
    client = TestClient(app)
    return client, service


def test_create_proof_point(api_client: Tuple[TestClient, FakeChromaIntegrationService]) -> None:
    client, service = api_client

    payload = {
        "profile_id": "user-123",
        "role_title": "Engineering Manager",
        "company": "TechCorp",
        "title": "Scaling the platform",
        "content": "Delivered a 10x improvement in release cadence.",
        "impact_tags": ["delivery", "leadership"],
        "status": "draft",
    }

    response = client.post("/proof-points", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    document_id = body["data"]["document_id"]
    assert document_id in service.proof_points
    assert service.proof_points[document_id]["impact_tags"] == ["delivery", "leadership"]


def test_resume_upload_and_approval_flow(
    api_client: Tuple[TestClient, FakeChromaIntegrationService]
) -> None:
    client, service = api_client

    resume_payload = {
        "profile_id": "user-123",
        "title": "Principal Engineer Resume",
        "content": "Extensive experience in scaling systems.",
        "job_target": "principal-engineer",
        "selected_proof_points": ["proof-1"],
    }

    first_response = client.post("/resumes", json=resume_payload)
    assert first_response.status_code == 200
    first_doc_id = first_response.json()["data"]["document_id"]

    second_payload = {
        **resume_payload,
        "title": "Principal Engineer Resume v2",
        "content": "Updated accomplishments and metrics.",
    }
    second_response = client.post("/resumes", json=second_payload)
    assert second_response.status_code == 200
    second_doc_id = second_response.json()["data"]["document_id"]

    assert service.resumes[first_doc_id]["metadata"]["is_latest"] is False
    assert service.resumes[second_doc_id]["metadata"]["is_latest"] is True

    approval_timestamp = datetime.now(UTC).isoformat()
    approval_payload = {
        "status": "approved",
        "approved_by": "reviewer@example.com",
        "approved_at": approval_timestamp,
        "approval_notes": "Looks great",
        "selected_proof_points": ["proof-1", "proof-2"],
        "is_latest": True,
    }

    approval_response = client.patch(
        f"/resumes/{first_doc_id}",
        json=approval_payload,
    )
    assert approval_response.status_code == 200
    approval_body = approval_response.json()
    assert approval_body["status"] == "success"

    metadata = approval_body["data"]["metadata"]
    assert metadata["status"] == "approved"
    assert metadata["approved_by"] == "reviewer@example.com"
    assert metadata["approved_at"].startswith(approval_timestamp[:19])
    assert metadata["is_latest"] is True
    assert metadata["version"] == 1
    assert metadata["selected_proof_points"] == ["proof-1", "proof-2"]
    assert metadata["status_transitions"][-1]["to"] == "approved"

    # Ensure the competing resume was demoted
    assert service.resumes[second_doc_id]["metadata"]["is_latest"] is False
    assert service.resumes[second_doc_id]["metadata"]["latest_version"] is False
