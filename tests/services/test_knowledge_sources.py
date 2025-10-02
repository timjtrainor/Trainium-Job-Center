"""
Tests for ChromaKnowledgeSource and knowledge source configuration.
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the correct path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python-service'))

from app.services.crewai.knowledge_sources import (
    ChromaKnowledgeSource,
    create_knowledge_source_from_config,
    get_knowledge_sources_from_config
)


class TestChromaKnowledgeSource:
    """Test cases for ChromaKnowledgeSource functionality."""

    @pytest.fixture
    def knowledge_source_config(self):
        """Sample knowledge source configuration."""
        return {
            "type": "chroma",
            "config": {
                "collection": "test_collection",
                "host": "chromadb",
                "port": 8001,
                "filters": {"section": "test_section", "latest_version": True},
                "top_k": 3
            }
        }

    def test_knowledge_source_creation_from_config(self, knowledge_source_config):
        """Test creating knowledge source from configuration."""
        ks = create_knowledge_source_from_config(knowledge_source_config)

        assert isinstance(ks, ChromaKnowledgeSource)
        assert ks.collection_name == "test_collection"
        assert ks.host == "chromadb"
        assert ks.port == 8001

    def test_invalid_knowledge_source_type(self):
        """Test error handling for invalid knowledge source types."""
        config = {
            "type": "invalid_type",
            "config": {}
        }

        with pytest.raises(ValueError, match="Unsupported knowledge source type"):
            create_knowledge_source_from_config(config)

    def test_multiple_knowledge_sources_from_config(self):
        """Test creating multiple knowledge sources from config list."""
        configs = [
            {
                "type": "chroma",
                "config": {
                    "collection": "collection1",
                    "host": "chromadb",
                    "port": 8001
                }
            },
            {
                "type": "chroma",
                "config": {
                    "collection": "collection2",
                    "host": "chromadb",
                    "port": 8001
                }
            }
        ]

        sources = get_knowledge_sources_from_config(configs)

        assert len(sources) == 2
        assert sources[0].collection_name == "collection1"
        assert sources[1].collection_name == "collection2"

    def test_content_validation_valid(self):
        """Test content validation for valid content."""
        ks = ChromaKnowledgeSource("test", host="chromadb", port=8001)

        assert ks.validate_content("Valid content")
        assert ks.validate_content("Multi-line\ncontent")

    def test_content_validation_invalid(self):
        """Test content validation for invalid content."""
        ks = ChromaKnowledgeSource("test", host="chromadb", port=8001)

        assert not ks.validate_content("")
        assert not ks.validate_content("   ")
        assert not ks.validate_content(123)  # Non-string content
        assert not ks.validate_content(None)

    @patch('app.services.crewai.knowledge_sources.ChromaService')
    def test_search_method(self, mock_chroma_service_cls, knowledge_source_config):
        """Test the search method uses ChromaDB correctly."""
        # Setup mock
        mock_chroma_service = Mock()
        mock_chroma_service_cls.return_value = mock_chroma_service

        # Mock similarity_search to return sample results
        mock_chroma_service.similarity_search.return_value = [
            {"content": "Sample content 1", "metadata": {"section": "test"}},
            {"content": "Sample content 2", "metadata": {"section": "test"}}
        ]

        # Create knowledge source and test search
        ks = create_knowledge_source_from_config(knowledge_source_config)
        results = ks.search("test query")

        assert results == ["Sample content 1", "Sample content 2"]
        mock_chroma_service.similarity_search.assert_called_once()

    @patch('app.services.crewai.knowledge_sources.ChromaService')
    def test_add_method(self, mock_chroma_service_cls):
        """Test the add method stores content in ChromaDB."""
        mock_chroma_service = Mock()
        mock_chroma_service_cls.return_value = mock_chroma_service

        metadata = {"custom": "metadata"}
        ks = ChromaKnowledgeSource("test_collection", host="chromadb", port=8001)
        ks.add("Test content", metadata=metadata)

        # Verify add_documents was called with correct parameters
        mock_chroma_service.add_documents.assert_called_once()
        call_args = mock_chroma_service.add_documents.call_args
        assert call_args.kwargs["collection_name"] == "test_collection"

        # Check that metadata was merged properly
        added_docs = call_args.kwargs["documents"]
        added_metadatas = call_args.kwargs["metadatas"]

        assert added_docs == ["Test content"]
        assert added_metadatas[0]["collection"] == "test_collection"
        assert added_metadatas[0]["custom"] == "metadata"


class TestKnowledgeSourceConfiguration:
    """Test knowledge source configuration parsing."""

    def test_config_with_filters(self):
        """Test configuration with metadata filters."""
        config = {
            "type": "chroma",
            "config": {
                "collection": "filtered_collection",
                "host": "custom.host",
                "port": 443,
                "filters": {
                    "section": "specific_section",
                    "version": "latest"
                },
                "top_k": 5
            }
        }

        ks = create_knowledge_source_from_config(config)

        assert ks.collection_name == "filtered_collection"
        assert ks.host == "custom.host"
        assert ks.port == 443
        assert ks.filters["section"] == "specific_section"
        assert ks.top_k == 5

    def test_default_values(self):
        """Test default values are applied correctly."""
        config = {
            "type": "chroma",
            "config": {
                "collection": "minimal_config"
            }
        }

        ks = create_knowledge_source_from_config(config)

        # Test defaults
        assert ks.collection_name == "minimal_config"
        assert ks.host == "chromadb"  # default host
        assert ks.port == 8001  # default port from our updated code
        assert ks.filters == {}  # default empty filters
        assert ks.top_k == 5  # default top_k
