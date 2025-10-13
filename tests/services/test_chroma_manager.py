"""Tests for the ChromaDB manager functionality."""

import pytest
from unittest.mock import MagicMock, patch

from python_service.app.services.chroma_manager import (
    ChromaCollectionConfig,
    ChromaManager,
    CollectionType,
    get_chroma_manager,
)


class MockCollection:
    """Mock ChromaDB collection."""

    def __init__(self, name: str, count: int = 0):
        self.name = name
        self._count = count
        self.metadata = {
            "purpose": "test",
            "embed_model": "mock:model",
            "created_at": "2024-01-01T00:00:00Z"
        }
        self.records = {}

    def count(self):
        return len(self.records)

    def add(self, ids, documents, metadatas):
        for idx, record_id in enumerate(ids):
            self.records[record_id] = {
                "document": documents[idx],
                "metadata": metadatas[idx]
            }
        self._count = len(self.records)

    def get(self, ids=None, where=None, include=None):
        include = include or []

        matched_ids = []
        matched_records = []

        for record_id, record in self.records.items():
            if ids and record_id not in ids:
                continue

            metadata = record["metadata"]
            if where:
                is_match = all(metadata.get(key) == value for key, value in where.items())
                if not is_match:
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

    def query(self, query_texts, n_results=5, where=None, include=None):
        include = include or []

        matched = {}
        for record in self.records.values():
            metadata = record["metadata"]
            if where:
                is_match = all(metadata.get(key) == value for key, value in where.items())
                if not is_match:
                    continue

            doc_id = metadata.get("doc_id")
            if not doc_id:
                continue

            current = matched.get(doc_id)
            if not current or metadata.get("version", 0) > current["metadata"].get("version", 0):
                matched[doc_id] = record

        selected = list(matched.values())[:n_results]
        documents = [[record["document"] for record in selected]]

        if not documents[0]:
            documents = [[]]

        result = {
            "documents": documents,
            "distances": [[0.0 for _ in documents[0]]] if documents and documents[0] else [[]]
        }

        if "metadatas" in include:
            result["metadatas"] = [[record["metadata"] for record in selected]]
        else:
            result["metadatas"] = [[]]

        return result


class MockClient:
    """Mock ChromaDB client."""
    
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
        if name not in self.collections:
            raise ValueError(f"Collection {name} not found")
        return self.collections[name]
    
    def list_collections(self):
        return [MagicMock(name=name, metadata=col.metadata) 
                for name, col in self.collections.items()]
    
    def delete_collection(self, name):
        if name in self.collections:
            del self.collections[name]
        else:
            raise ValueError(f"Collection {name} not found")


@pytest.fixture
def mock_chroma_client():
    """Fixture providing a mock ChromaDB client."""
    return MockClient()


@pytest.fixture
def mock_embedding_function():
    """Fixture providing a mock embedding function."""
    return MagicMock()


class TestChromaManager:
    """Test suite for ChromaManager functionality."""
    
    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    def test_initialization(self, mock_get_embedding, mock_get_client, mock_chroma_client, mock_embedding_function):
        """Test ChromaManager initialization."""
        mock_get_client.return_value = mock_chroma_client
        mock_get_embedding.return_value = mock_embedding_function
        
        manager = ChromaManager()
        
        # Test that default collections are registered
        configs = manager.list_registered_collections()
        assert len(configs) >= 4  # At least our default collections
        
        collection_names = [config.name for config in configs]
        assert "job_postings" in collection_names
        assert "company_profiles" in collection_names
        assert "career_brand" in collection_names
        assert "proof_points" in collection_names
        assert "resumes" in collection_names
        assert "documents" in collection_names
    
    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    @pytest.mark.asyncio
    async def test_ensure_collection_exists(self, mock_get_embedding, mock_get_client, mock_chroma_client, mock_embedding_function):
        """Test collection creation."""
        mock_get_client.return_value = mock_chroma_client
        mock_get_embedding.return_value = mock_embedding_function
        
        manager = ChromaManager()
        await manager.initialize()
        
        # Test creating a new collection
        result = await manager.ensure_collection_exists("test_collection")
        assert result is True
        assert "test_collection" in mock_chroma_client.collections
    
    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    @pytest.mark.asyncio
    async def test_upload_document(self, mock_get_embedding, mock_get_client, mock_chroma_client, mock_embedding_function):
        """Test document upload functionality."""
        mock_get_client.return_value = mock_chroma_client
        mock_get_embedding.return_value = mock_embedding_function
        
        manager = ChromaManager()
        await manager.initialize()
        
        # Upload a test document
        result = await manager.upload_document(
            collection_name="test_collection",
            title="Test Document",
            document_text="This is a test document with some content for testing.",
            metadata={"test_field": "test_value"},
            tags=["test", "document"]
        )
        
        assert result.success is True
        assert result.collection_name == "test_collection"
        assert result.chunks_created > 0
        assert len(result.document_id) > 0
    
    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    @pytest.mark.asyncio
    async def test_search_collection(self, mock_get_embedding, mock_get_client, mock_chroma_client, mock_embedding_function):
        """Test collection search functionality."""
        mock_get_client.return_value = mock_chroma_client
        mock_get_embedding.return_value = mock_embedding_function
        
        manager = ChromaManager()
        await manager.initialize()
        
        # Create a collection with some content
        await manager.ensure_collection_exists("test_collection")
        
        # Perform search
        result = await manager.search_collection(
            collection_name="test_collection",
            query="test query",
            n_results=3
        )
        
        assert result["success"] is True
        assert result["collection_name"] == "test_collection"
        assert len(result["documents"]) > 0
    
    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    @pytest.mark.asyncio
    async def test_search_across_collections(self, mock_get_embedding, mock_get_client, mock_chroma_client, mock_embedding_function):
        """Test cross-collection search functionality."""
        mock_get_client.return_value = mock_chroma_client
        mock_get_embedding.return_value = mock_embedding_function
        
        manager = ChromaManager()
        await manager.initialize()
        
        # Create multiple collections
        await manager.ensure_collection_exists("collection1")
        await manager.ensure_collection_exists("collection2")
        
        # Perform cross-collection search
        result = await manager.search_across_collections(
            query="test query",
            collection_names=["collection1", "collection2"],
            n_results=2
        )
        
        assert result["success"] is True
        assert "collection1" in result["results"]
        assert "collection2" in result["results"]
    
    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    @pytest.mark.asyncio
    async def test_list_all_collections(self, mock_get_embedding, mock_get_client, mock_chroma_client, mock_embedding_function):
        """Test listing all collections."""
        mock_get_client.return_value = mock_chroma_client
        mock_get_embedding.return_value = mock_embedding_function
        
        manager = ChromaManager()
        await manager.initialize()
        
        # Create some test collections
        await manager.ensure_collection_exists("test1")
        await manager.ensure_collection_exists("test2")
        
        # List collections
        collections = await manager.list_all_collections()
        
        assert len(collections) >= 2
        collection_names = [col.name for col in collections]
        assert "test1" in collection_names
        assert "test2" in collection_names
    
    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    @pytest.mark.asyncio
    async def test_delete_collection(self, mock_get_embedding, mock_get_client, mock_chroma_client, mock_embedding_function):
        """Test collection deletion."""
        mock_get_client.return_value = mock_chroma_client
        mock_get_embedding.return_value = mock_embedding_function
        
        manager = ChromaManager()
        await manager.initialize()
        
        # Create and then delete a collection
        await manager.ensure_collection_exists("test_delete")
        assert "test_delete" in mock_chroma_client.collections
        
        result = await manager.delete_collection("test_delete")
        assert result is True
        assert "test_delete" not in mock_chroma_client.collections
    
    def test_collection_config_registration(self):
        """Test custom collection configuration registration."""
        manager = ChromaManager()
        
        # Register a custom collection config
        custom_config = ChromaCollectionConfig(
            name="custom_collection",
            collection_type=CollectionType.GENERIC_DOCUMENTS,
            description="Custom test collection",
            chunk_size=500,
            chunk_overlap=100
        )
        
        manager.register_collection_config(custom_config)
        
        # Verify it was registered
        retrieved_config = manager.get_collection_config("custom_collection")
        assert retrieved_config is not None
        assert retrieved_config.name == "custom_collection"
        assert retrieved_config.chunk_size == 500
        assert retrieved_config.chunk_overlap == 100
    
    def test_singleton_manager(self):
        """Test that get_chroma_manager returns a singleton."""
        manager1 = get_chroma_manager()
        manager2 = get_chroma_manager()

        assert manager1 is manager2  # Same instance

    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    @pytest.mark.asyncio
    async def test_career_brand_versioning_sets_single_latest(
        self,
        mock_get_embedding,
        mock_get_client,
        mock_chroma_client,
        mock_embedding_function
    ):
        """Ensure only the latest career brand narrative retains the is_latest flag."""

        mock_get_client.return_value = mock_chroma_client
        mock_get_embedding.return_value = mock_embedding_function

        manager = ChromaManager()

        profile_id = "profile-123"
        section = "north_star_vision"

        result_v1 = await manager.upload_career_brand_document(
            section=section,
            content="First vision",
            title="North Star",
            narrative_id=profile_id
        )
        assert result_v1.success

        result_v2 = await manager.upload_career_brand_document(
            section=section,
            content="Updated vision",
            title="North Star",
            narrative_id=profile_id
        )
        assert result_v2.success

        collection = mock_chroma_client.get_collection("career_brand")
        stored = collection.get(
            where={"profile_id": profile_id, "section": section},
            include=["metadatas"]
        )

        latest_flags = {}
        versions = {}
        for metadata in stored.get("metadatas", []):
            doc_id = metadata.get("doc_id")
            if not doc_id or doc_id in latest_flags:
                continue
            latest_flags[doc_id] = metadata.get("is_latest")
            versions[doc_id] = metadata.get("version")

        assert set(latest_flags.keys()) == {result_v1.document_id, result_v2.document_id}
        assert latest_flags[result_v1.document_id] is False
        assert latest_flags[result_v2.document_id] is True
        assert versions[result_v2.document_id] == 2

    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    @pytest.mark.asyncio
    async def test_proof_point_versioning_enforces_single_latest(
        self,
        mock_get_embedding,
        mock_get_client,
        mock_chroma_client,
        mock_embedding_function
    ):
        """Ensure proof point uploads toggle is_latest across versions."""

        mock_get_client.return_value = mock_chroma_client
        mock_get_embedding.return_value = mock_embedding_function

        manager = ChromaManager()

        result_v1 = await manager.upload_proof_point_document(
            profile_id="profile-456",
            role_title="Product Manager",
            job_title="Product Manager - Launch",
            location="Remote",
            start_date="2021-01-01",
            end_date="2021-12-31",
            is_current=False,
            company="OpenAI",
            content="Delivered first version",
            title="Launch",
            status="published",
            impact_tags=["launch"]
        )
        assert result_v1.success

        result_v2 = await manager.upload_proof_point_document(
            profile_id="profile-456",
            role_title="Product Manager",
            job_title="Product Manager - Launch",
            location="Remote",
            start_date="2021-01-01",
            end_date="2021-12-31",
            is_current=False,
            company="OpenAI",
            content="Improved performance",
            title="Launch",
            status="published",
            impact_tags=["performance"]
        )
        assert result_v2.success

        collection = mock_chroma_client.get_collection("proof_points")
        stored = collection.get(
            where={
                "profile_id": "profile-456",
                "company": "OpenAI",
                "job_title": "Product Manager - Launch",
                "location": "Remote",
                "start_date": "2021-01-01",
                "end_date": "2021-12-31",
                "is_current": False,
            },
            include=["metadatas"]
        )

        latest_flags = {}
        start_dates = {}
        for metadata in stored.get("metadatas", []):
            doc_id = metadata.get("doc_id")
            if not doc_id or doc_id in latest_flags:
                continue
            latest_flags[doc_id] = metadata.get("is_latest")
            start_dates[doc_id] = metadata.get("start_date")
            assert metadata.get("job_title") == "Product Manager - Launch"
            assert metadata.get("location") == "Remote"
            assert metadata.get("end_date") == "2021-12-31"
            assert metadata.get("is_current") is False

        assert set(latest_flags.keys()) == {result_v1.document_id, result_v2.document_id}
        assert latest_flags[result_v1.document_id] is False
        assert latest_flags[result_v2.document_id] is True
        assert start_dates[result_v1.document_id] == "2021-01-01"

    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    @pytest.mark.asyncio
    async def test_resume_versioning_enforces_single_latest(
        self,
        mock_get_embedding,
        mock_get_client,
        mock_chroma_client,
        mock_embedding_function
    ):
        """Ensure resume uploads retain a single latest document per job target."""

        mock_get_client.return_value = mock_chroma_client
        mock_get_embedding.return_value = mock_embedding_function

        manager = ChromaManager()

        result_v1 = await manager.upload_resume_document(
            profile_id="profile-789",
            job_target="AI PM",
            content="Resume v1",
            title="AI PM Resume",
            status="draft",
            selected_proof_points=["proof-1"]
        )
        assert result_v1.success

        result_v2 = await manager.upload_resume_document(
            profile_id="profile-789",
            job_target="AI PM",
            content="Resume v2",
            title="AI PM Resume",
            status="ready",
            selected_proof_points=["proof-1", "proof-2"]
        )
        assert result_v2.success

        collection = mock_chroma_client.get_collection("resumes")
        stored = collection.get(
            where={"profile_id": "profile-789", "job_target": "AI PM"},
            include=["metadatas"]
        )

        latest_flags = {}
        selected_points = {}
        for metadata in stored.get("metadatas", []):
            doc_id = metadata.get("doc_id")
            if not doc_id or doc_id in latest_flags:
                continue
            latest_flags[doc_id] = metadata.get("is_latest")
            selected_points[doc_id] = metadata.get("selected_proof_points")

        assert set(latest_flags.keys()) == {result_v1.document_id, result_v2.document_id}
        assert latest_flags[result_v1.document_id] is False
        assert latest_flags[result_v2.document_id] is True
        assert selected_points[result_v2.document_id] == ["proof-1", "proof-2"]

    @patch('app.services.chroma_manager.get_chroma_client')
    @patch('app.services.chroma_manager.get_embedding_function')
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_get_embedding, mock_get_client):
        """Test error handling in various scenarios."""
        # Test client connection failure
        mock_get_client.side_effect = Exception("Connection failed")
        
        manager = ChromaManager()
        
        result = await manager.search_collection("test", "query")
        assert result["success"] is False
        assert "Connection failed" in result["error"]