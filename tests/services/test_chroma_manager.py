"""Tests for the ChromaDB manager functionality."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from python_service.app.services.chroma_manager import ChromaManager, ChromaCollectionConfig, CollectionType, get_chroma_manager


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
    
    def count(self):
        return self._count
    
    def add(self, ids, documents, metadatas):
        self._count += len(documents)
    
    def query(self, query_texts, n_results=5, where=None, include=None):
        # Return mock search results
        return {
            "documents": [["Mock document content for: " + query_texts[0]]],
            "metadatas": [[{"title": "Mock Document", "type": "test"}]],
            "distances": [[0.1]]
        }


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
    async def test_error_handling(self, mock_get_embedding, mock_get_client):
        """Test error handling in various scenarios."""
        # Test client connection failure
        mock_get_client.side_effect = Exception("Connection failed")
        
        manager = ChromaManager()
        
        result = await manager.search_collection("test", "query")
        assert result["success"] is False
        assert "Connection failed" in result["error"]