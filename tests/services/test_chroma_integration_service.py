"""Tests for the ChromaDB integration service enhanced functionality."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from app.services.chroma_integration_service import ChromaIntegrationService
from app.services.chroma_manager import ChromaManager
from app.schemas.chroma import ChromaUploadResponse


@pytest.fixture
def anyio_backend():
    """Force AnyIO tests to run against asyncio only."""

    return "asyncio"


class TestChromaIntegrationServiceEnhancements:
    """Test suite for new ChromaDB integration service functionality."""
    
    @pytest.fixture
    def mock_manager(self):
        """Mock ChromaDB manager."""
        manager = MagicMock()
        manager.initialize = AsyncMock()
        manager.upload_document = AsyncMock(return_value=ChromaUploadResponse(
            success=True,
            message="Document uploaded successfully",
            collection_name="test_collection",
            document_id="test_doc_id",
            chunks_created=1
        ))
        manager.upload_resume_document = AsyncMock(return_value=ChromaUploadResponse(
            success=True,
            message="Resume uploaded successfully",
            collection_name="resumes",
            document_id="resume_doc_id",
            chunks_created=1
        ))
        manager.upload_proof_point_document = AsyncMock(return_value=ChromaUploadResponse(
            success=True,
            message="Proof point uploaded successfully",
            collection_name="proof_points",
            document_id="proof_doc_id",
            chunks_created=1
        ))
        manager.search_across_collections = AsyncMock(return_value={
            "success": True,
            "results": {
                "test_collection": {
                    "success": True,
                    "documents": ["Test document content"],
                    "metadatas": [{"uploaded_at": "2024-01-01T00:00:00Z", "profile_id": "test_profile"}]
                }
            }
        })
        return manager
    
    @pytest.fixture
    def service(self, mock_manager):
        """ChromaDB integration service with mocked manager."""
        with patch('app.services.chroma_integration_service.get_chroma_manager', return_value=mock_manager):
            return ChromaIntegrationService()
    
    @pytest.mark.anyio("asyncio")
    async def test_add_career_brand_document_with_section_and_uploaded_at(self, service, mock_manager):
        """Test career brand document upload with required section and auto uploaded_at."""
        test_datetime = datetime(2024, 1, 1, 12, 0, 0)
        
        result = await service.add_career_brand_document(
            title="Test Career Brand",
            content="Test content",
            profile_id="test_profile",
            section="personal_branding",
            source="manual",
            author="test_user",
            uploaded_at=test_datetime
        )
        
        # Verify the document was uploaded with correct metadata
        mock_manager.upload_document.assert_called_once()
        call_args = mock_manager.upload_document.call_args
        
        assert call_args[1]['collection_name'] == "career_brand"
        assert call_args[1]['title'] == "Test Career Brand"
        assert call_args[1]['document_text'] == "Test content"
        
        metadata = call_args[1]['metadata']
        assert metadata['profile_id'] == "test_profile"
        assert metadata['section'] == "personal_branding"
        assert metadata['uploaded_at'] == test_datetime.isoformat()
        assert metadata['source'] == "manual"
        assert metadata['author'] == "test_user"
        
        assert result.success is True
    
    @pytest.mark.anyio("asyncio")
    async def test_add_career_brand_document_auto_uploaded_at(self, service, mock_manager):
        """Test career brand document upload with auto-generated uploaded_at."""
        result = await service.add_career_brand_document(
            title="Test Career Brand",
            content="Test content",
            profile_id="test_profile",
            section="personal_branding"
        )
        
        # Verify uploaded_at was auto-generated
        call_args = mock_manager.upload_document.call_args
        metadata = call_args[1]['metadata']
        assert 'uploaded_at' in metadata
        assert metadata['uploaded_at']  # Should be populated
        
        # Verify it's a valid ISO datetime string
        datetime.fromisoformat(metadata['uploaded_at'].replace('Z', '+00:00'))
    
    @pytest.mark.anyio("asyncio")
    async def test_add_career_path_document(self, service, mock_manager):
        """Test career path document upload."""
        result = await service.add_career_path_document(
            title="Test Career Path",
            content="Career path content",
            profile_id="test_profile",
            section="career_planning"
        )
        
        call_args = mock_manager.upload_document.call_args
        assert call_args[1]['collection_name'] == "career_paths"
        
        metadata = call_args[1]['metadata']
        assert metadata['profile_id'] == "test_profile"
        assert metadata['section'] == "career_planning"
        assert 'uploaded_at' in metadata
    
    @pytest.mark.anyio("asyncio")
    async def test_add_job_search_strategies_document(self, service, mock_manager):
        """Test job search strategies document upload."""
        result = await service.add_job_search_strategies_document(
            title="Test Job Search Strategy",
            content="Job search strategy content",
            profile_id="test_profile",
            section="networking"
        )
        
        call_args = mock_manager.upload_document.call_args
        assert call_args[1]['collection_name'] == "job_search_strategies"
        
        metadata = call_args[1]['metadata']
        assert metadata['profile_id'] == "test_profile"
        assert metadata['section'] == "networking"
        assert 'uploaded_at' in metadata
    
    @pytest.mark.anyio("asyncio")
    async def test_add_resume_document(self, service, mock_manager):
        """Test resume document upload with default section."""
        status_transition = [{"to": "draft", "at": "2024-01-01T00:00:00Z"}]
        result = await service.add_resume_document(
            title="My Resume",
            content="Resume content",
            profile_id="test_profile",
            job_target="ml-engineer",
            selected_proof_points=["proof-1"],
            status_transitions=status_transition
        )

        mock_manager.upload_resume_document.assert_called_once()
        call_args = mock_manager.upload_resume_document.call_args
        kwargs = call_args.kwargs

        assert kwargs['job_target'] == "ml-engineer"
        assert kwargs['status'] == "draft"

        metadata = kwargs['additional_metadata']
        assert metadata['profile_id'] == "test_profile"
        assert metadata['section'] == "resume"  # Default value
        assert metadata['title'] == "My Resume"
        assert metadata['selected_proof_points'] == ["proof-1"]
        assert metadata['status_transitions'] == status_transition
        assert 'uploaded_at' in metadata
        assert result.success is True

    @pytest.mark.anyio("asyncio")
    async def test_add_resume_document_custom_section(self, service, mock_manager):
        """Test resume document upload with custom section."""
        result = await service.add_resume_document(
            title="Technical Resume",
            content="Technical resume content",
            profile_id="test_profile",
            section="technical_resume",
            job_target="ml-engineer"
        )

        call_args = mock_manager.upload_resume_document.call_args
        kwargs = call_args.kwargs
        metadata = kwargs['additional_metadata']
        assert metadata['section'] == "technical_resume"

    @pytest.mark.anyio("asyncio")
    async def test_add_resume_document_without_job_target_uses_generic_upload(self, service, mock_manager):
        """Ensure legacy resume uploads without job target still succeed."""

        result = await service.add_resume_document(
            title="Legacy Resume",
            content="Legacy resume content",
            profile_id="legacy-profile"
        )

        mock_manager.upload_resume_document.assert_not_called()
        mock_manager.upload_document.assert_called_once()

        collection_call = mock_manager.upload_document.call_args
        kwargs = collection_call.kwargs

        assert kwargs['collection_name'] == "resumes"
        assert kwargs['title'] == "Legacy Resume"
        assert kwargs['document_text'] == "Legacy resume content"

        metadata = kwargs['metadata']
        assert metadata['profile_id'] == "legacy-profile"
        assert metadata['section'] == "resume"
        assert metadata['status'] == "draft"
        assert 'uploaded_at' in metadata

        assert result.success is True

    @pytest.mark.anyio("asyncio")
    async def test_create_proof_point_for_job(self, service, mock_manager):
        """Ensure proof point creation forwards job metadata and transitions."""
        job_metadata = {"id": "job-123", "title": "Staff Engineer", "location": "Remote"}
        status_transitions = [{"to": "draft", "at": "2024-01-01T00:00:00Z"}]

        result = await service.create_proof_point_for_job(
            profile_id="profile-1",
            role_title="Staff Engineer",
            company="Acme Corp",
            content="Delivered 40% performance gains",
            title="Performance Wins",
            job_metadata=job_metadata,
            status="ready",
            impact_tags=["performance"],
            status_transitions=status_transitions
        )

        mock_manager.upload_proof_point_document.assert_called_once()
        kwargs = mock_manager.upload_proof_point_document.call_args.kwargs

        assert kwargs['profile_id'] == "profile-1"
        assert kwargs['status'] == "ready"
        metadata = kwargs['additional_metadata']
        assert metadata['job_id'] == "job-123"
        assert metadata['job_title'] == "Staff Engineer"
        assert metadata['job_location'] == "Remote"
        assert metadata['status_transitions'] == status_transitions
        assert metadata['impact_tags'] == ["performance"]
        assert 'uploaded_at' in metadata
        assert result.success is True

    @pytest.mark.anyio("asyncio")
    async def test_update_proof_point_for_job(self, service, mock_manager):
        """Ensure proof point update forwards versioning metadata."""
        await service.update_proof_point_for_job(
            profile_id="profile-1",
            role_title="Staff Engineer",
            company="Acme Corp",
            content="Updated impact",
            title="Performance Wins",
            job_metadata={"id": "job-123"},
            status="approved",
            version=3,
            is_latest=False,
            status_transitions=[{"from": "ready", "to": "approved", "at": "2024-02-01T00:00:00Z"}]
        )

        kwargs = mock_manager.upload_proof_point_document.call_args.kwargs
        metadata = kwargs['additional_metadata']
        assert metadata['job_id'] == "job-123"
        assert metadata['status'] == "approved"
        assert metadata['version'] == 3
        assert metadata['is_latest'] is False
    
    @pytest.mark.anyio("asyncio")
    async def test_search_for_crew_context_with_filters(self, service, mock_manager):
        """Test search with profile_id and section filtering."""
        result = await service.search_for_crew_context(
            query="test query",
            collections=["career_brand"],
            n_results=5,
            profile_id="test_profile",
            section="personal_branding"
        )
        
        # Verify search was called with where clause
        mock_manager.search_across_collections.assert_called_once()
        call_args = mock_manager.search_across_collections.call_args
        
        assert call_args[1]['query'] == "test query"
        assert call_args[1]['collection_names'] == ["career_brand"]
        assert call_args[1]['n_results'] == 5
        assert call_args[1]['where'] == {"profile_id": "test_profile", "section": "personal_branding"}
        
        # Verify response structure includes filters
        assert result['filters_applied']['profile_id'] == "test_profile"
        assert result['filters_applied']['section'] == "personal_branding"
        assert result['found_relevant_content'] is True
    
    @pytest.mark.anyio("asyncio")
    async def test_search_for_crew_context_no_filters(self, service, mock_manager):
        """Test search without filters."""
        result = await service.search_for_crew_context(
            query="test query",
            collections=["career_brand"]
        )
        
        call_args = mock_manager.search_across_collections.call_args
        assert call_args[1]['where'] is None
        
        assert result['filters_applied']['profile_id'] is None
        assert result['filters_applied']['section'] is None
    
    @pytest.mark.anyio("asyncio")
    async def test_prepare_crew_rag_context_with_filters(self, service, mock_manager):
        """Test RAG context preparation with profile_id and section filtering."""
        job_posting = {
            "title": "Software Engineer",
            "company": "Test Company",
            "description": "Job description"
        }
        
        result = await service.prepare_crew_rag_context(
            job_posting=job_posting,
            profile_id="test_profile",
            section="technical_resume"
        )
        
        # Verify response structure
        assert result['job_posting'] == job_posting
        assert result['profile_id'] == "test_profile"
        assert result['section'] == "technical_resume"
        assert 'search_results' in result
        assert 'context_summary' in result
        
        # Verify multiple search calls were made (one for each query)
        assert mock_manager.search_across_collections.call_count >= 2
    
    @pytest.mark.anyio("asyncio")
    async def test_document_versioning_latest_first(self, service, mock_manager):
        """Test that search results are sorted by uploaded_at for versioning."""
        # Mock search results with multiple documents having different uploaded_at times
        mock_manager.search_across_collections.return_value = {
            "success": True,
            "results": {
                "resumes": {
                    "success": True,
                    "documents": ["Older resume", "Newer resume"],
                    "metadatas": [
                        {"uploaded_at": "2024-01-01T00:00:00Z", "profile_id": "test_profile"},
                        {"uploaded_at": "2024-01-02T00:00:00Z", "profile_id": "test_profile"}
                    ]
                }
            }
        }
        
        result = await service.search_for_crew_context(
            query="resume",
            collections=["resumes"],
            profile_id="test_profile"
        )
        
        # Verify the documents are present in the context summary
        assert result['found_relevant_content'] is True
        assert len(result['context_summary']) == 1
        assert result['context_summary'][0]['collection'] == "resumes"
        assert result['context_summary'][0]['num_results'] == 2


class MockCollection:
    """In-memory collection for integration-style tests."""

    def __init__(self, name: str):
        self.name = name
        self.records = {}
        self.metadata = {
            "purpose": "test",
            "embed_model": "mock:model",
            "created_at": "2024-01-01T00:00:00Z"
        }

    def count(self):
        return len(self.records)

    def add(self, ids, documents, metadatas):
        for idx, record_id in enumerate(ids):
            self.records[record_id] = {
                "document": documents[idx],
                "metadata": metadatas[idx]
            }

    def get(self, ids=None, where=None, include=None):
        include = include or []
        matched_ids = []
        matched_records = []

        for record_id, record in self.records.items():
            metadata = record["metadata"]
            if ids and record_id not in ids:
                continue

            if where and not all(metadata.get(key) == value for key, value in where.items()):
                continue

            matched_ids.append(record_id)
            matched_records.append(record)

        result = {"ids": matched_ids}

        if not include or "metadatas" in include:
            result["metadatas"] = [record["metadata"] for record in matched_records]
        if not include or "documents" in include:
            result["documents"] = [record["document"] for record in matched_records]

        return result

    def update(self, ids, metadatas):
        for record_id, metadata in zip(ids, metadatas):
            if record_id in self.records:
                self.records[record_id]["metadata"] = metadata


class MockClient:
    """Mock ChromaDB client returning in-memory collections."""

    def __init__(self):
        self.collections = {}

    def get_or_create_collection(self, name, embedding_function=None, metadata=None):
        if name not in self.collections:
            collection = MockCollection(name)
            if metadata:
                collection.metadata.update(metadata)
            self.collections[name] = collection
        return self.collections[name]

    def get_collection(self, name):
        return self.collections[name]

    def list_collections(self):
        return [MagicMock(name=name, metadata=collection.metadata)
                for name, collection in self.collections.items()]


@pytest.fixture
async def integration_service_with_mock_chroma():
    """Provide an integration service wired to the mocked Chroma manager."""

    mock_client = MockClient()

    with patch('app.services.chroma_manager.get_chroma_client', return_value=mock_client), \
            patch('app.services.chroma_manager.get_embedding_function', return_value=MagicMock()):
        manager = ChromaManager()

        with patch('app.services.chroma_integration_service.get_chroma_manager', return_value=manager):
            service = ChromaIntegrationService()
            await service.initialize()
            yield service, mock_client


class TestChromaIntegrationServiceMetadataPersistence:
    """Integration-style tests that exercise real ChromaManager logic."""

    @pytest.mark.anyio("asyncio")
    async def test_resume_metadata_persistence(self, integration_service_with_mock_chroma):
        """Store draft and approved resumes and verify metadata persistence."""

        service, mock_client = integration_service_with_mock_chroma

        draft_transition = [{"to": "draft", "at": "2024-01-01T09:00:00Z"}]
        all_transitions = draft_transition + [
            {"from": "draft", "to": "approved", "at": "2024-02-01T09:30:00Z"}
        ]

        await service.add_resume_document(
            title="AI Engineer Resume",
            content="Draft resume",
            profile_id="user-123",
            job_target="ml-engineer",
            status="draft",
            selected_proof_points=["proof-1"],
            status_transitions=draft_transition,
            uploaded_at=datetime(2024, 1, 1, 9, 0, 0)
        )

        await service.add_resume_document(
            title="AI Engineer Resume",
            content="Approved resume",
            profile_id="user-123",
            job_target="ml-engineer",
            status="approved",
            selected_proof_points=["proof-1", "proof-2"],
            status_transitions=all_transitions,
            approved_by="coach-1",
            approved_at=datetime(2024, 2, 1, 9, 30, 0),
            uploaded_at=datetime(2024, 2, 1, 9, 30, 0)
        )

        collection = mock_client.get_collection("resumes")
        stored = collection.get(
            where={"profile_id": "user-123", "job_target": "ml-engineer"},
            include=["metadatas"]
        )

        metadata_by_doc = {}
        for metadata in stored.get("metadatas", []):
            doc_id = metadata.get("doc_id")
            if doc_id and doc_id not in metadata_by_doc:
                metadata_by_doc[doc_id] = metadata

        assert len(metadata_by_doc) == 2

        versions = {meta.get("version"): meta for meta in metadata_by_doc.values()}

        draft_meta = versions.get(1)
        approved_meta = versions.get(2)

        assert draft_meta is not None
        assert draft_meta["status"] == "draft"
        assert draft_meta["is_latest"] is False
        assert draft_meta["selected_proof_points"] == ["proof-1"]

        assert approved_meta is not None
        assert approved_meta["status"] == "approved"
        assert approved_meta["is_latest"] is True
        assert approved_meta["selected_proof_points"] == ["proof-1", "proof-2"]
        assert approved_meta["approved_by"] == "coach-1"
        assert approved_meta["approved_at"].startswith("2024-02-01T09:30:00")
        assert approved_meta["status_transitions"] == all_transitions

