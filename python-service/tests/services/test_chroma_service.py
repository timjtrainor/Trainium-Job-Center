"""Tests for ChromaDB service functionality."""

import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.chroma_service import ChromaService
from app.schemas.chroma import ChromaUploadRequest


class TestChromaService:
    """Test cases for ChromaService."""
    
    @pytest.fixture
    def chroma_service(self):
        """Create a ChromaService instance for testing."""
        with patch(
            "app.services.chroma_service.embedding_functions.SentenceTransformerEmbeddingFunction"
        ) as MockEmbedding:
            MockEmbedding.return_value = MagicMock()
            service = ChromaService()
        return service
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample upload request."""
        return ChromaUploadRequest(
            collection_name="test_collection",
            title="Test Document",
            tags=["test", "sample"],
            document_text="This is a test document with some content for testing purposes."
        )
    
    def test_chunk_text_basic(self, chroma_service):
        """Test basic text chunking functionality."""
        text = "This is a test " * 50  # 200 words
        chunks = chroma_service._chunk_text(text, words_per_chunk=30, overlap=5)
        
        assert len(chunks) > 1
        assert all(len(chunk.split()) <= 30 for chunk in chunks)
    
    def test_chunk_text_short(self, chroma_service):
        """Test chunking with text shorter than chunk size."""
        text = "Short text"
        chunks = chroma_service._chunk_text(text, words_per_chunk=30)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_sha1_hash(self, chroma_service):
        """Test SHA1 hash generation."""
        text = "test content"
        hash1 = chroma_service._sha1_hash(text)
        hash2 = chroma_service._sha1_hash(text)
        hash3 = chroma_service._sha1_hash("different content")
        
        assert hash1 == hash2  # Same content should produce same hash
        assert hash1 != hash3  # Different content should produce different hash
        assert len(hash1) == 40  # SHA1 produces 40-character hex string
    
    @patch('app.services.chroma_service.get_chroma_client')
    def test_upload_document_success(self, mock_get_client, chroma_service, sample_request):
        """Test successful document upload."""
        # Mock ChromaDB client and collection
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client

        # Execute upload
        result = asyncio.run(chroma_service.upload_document(sample_request))
        
        # Verify result
        assert result.success is True
        assert result.collection_name == sample_request.collection_name
        assert result.chunks_created > 0
        assert result.document_id != ""

        # Verify client was called correctly
        mock_client.get_or_create_collection.assert_called_once()
        mock_collection.add.assert_called_once()
        _, kwargs = mock_collection.add.call_args
        metadatas = kwargs["metadatas"]
        assert all(isinstance(md["tags"], str) for md in metadatas)
        assert metadatas[0]["tags"] == "test, sample"
    
    @patch('app.services.chroma_service.get_chroma_client')
    def test_upload_document_failure(self, mock_get_client, chroma_service, sample_request):
        """Test document upload failure handling."""
        # Mock ChromaDB client to raise an exception
        mock_get_client.side_effect = Exception("ChromaDB connection failed")

        # Execute upload
        result = asyncio.run(chroma_service.upload_document(sample_request))
        
        # Verify failure response
        assert result.success is False
        assert "ChromaDB connection failed" in result.message
        assert result.chunks_created == 0
    
    @patch('app.services.chroma_service.get_chroma_client')
    def test_list_collections(self, mock_get_client, chroma_service):
        """Test listing collections."""
        # Mock ChromaDB client and collections
        mock_client = Mock()
        mock_collection_info = Mock()
        mock_collection_info.name = "test_collection"
        mock_collection_info.metadata = {"purpose": "test"}
        
        mock_collection = Mock()
        mock_collection.count.return_value = 5
        
        mock_client.list_collections.return_value = [mock_collection_info]
        mock_client.get_collection.return_value = mock_collection
        mock_get_client.return_value = mock_client
        
        # Execute list collections
        result = asyncio.run(chroma_service.list_collections())
        
        # Verify result
        assert len(result) == 1
        assert result[0].name == "test_collection"
        assert result[0].count == 5
        assert result[0].metadata == {"purpose": "test"}
    
    @patch('app.services.chroma_service.get_chroma_client')
    def test_delete_collection_success(self, mock_get_client, chroma_service):
        """Test successful collection deletion."""
        # Mock ChromaDB client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Execute delete
        result = asyncio.run(chroma_service.delete_collection("test_collection"))
        
        # Verify result
        assert result is True
        mock_client.delete_collection.assert_called_once_with("test_collection")
    
    @patch('app.services.chroma_service.get_chroma_client')
    def test_delete_collection_failure(self, mock_get_client, chroma_service):
        """Test collection deletion failure handling."""
        # Mock ChromaDB client to raise an exception
        mock_client = Mock()
        mock_client.delete_collection.side_effect = Exception("Collection not found")
        mock_get_client.return_value = mock_client
        
        # Execute delete
        result = asyncio.run(chroma_service.delete_collection("nonexistent_collection"))

        # Verify failure
        assert result is False

