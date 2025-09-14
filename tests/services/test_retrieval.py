"""
Unit tests for retrieval functions.

Tests the retrieval layer that prepares inputs for YAML-defined CrewAI tasks,
including job description normalization and ChromaDB career brand queries.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.fit_review.retrieval import (
    normalize_jd,
    get_career_brand_digest,
    build_context,
    _extract_tags
)


class TestNormalizeJd:
    """Test job description normalization functionality."""
    
    def test_normalize_jd_strips_html_and_dedupes_bullets(self):
        """
        Test HTML stripping and bullet deduplication.
        
        Uses Bleach and selectolax for safe HTML removal as referenced in the code.
        Verifies whitespace normalization and duplicate line removal.
        """
        html_jd = """
        <h1>Software Engineer</h1>
        <p>We are looking for a <strong>senior developer</strong></p>
        <ul>
            <li>Experience with Python</li>
            <li>Experience with JavaScript</li>
            <li>Experience with Python</li>  <!-- duplicate -->
        </ul>
        <div>
            <p>Requirements:</p>
            <ul>
                <li>5+ years experience</li>
                <li>Bachelor's degree</li>
            </ul>
        </div>
        """
        
        result = normalize_jd(html_jd)
        
        # HTML tags should be removed (Bleach/selectolax functionality)
        assert '<' not in result
        assert '>' not in result
        assert '<h1>' not in result
        assert '<strong>' not in result
        
        # Content should be preserved
        assert 'Software Engineer' in result
        assert 'senior developer' in result
        assert 'Experience with Python' in result
        assert 'Experience with JavaScript' in result
        assert '5+ years experience' in result
        
        # Duplicates should be removed - "Experience with Python" appears only once
        python_mentions = result.count('Experience with Python')
        assert python_mentions == 1, f"Expected 1 mention of 'Experience with Python', got {python_mentions}"
        
        # Whitespace should be normalized
        assert '  ' not in result  # No double spaces
        assert '\n\n\n' not in result  # No triple newlines
    
    def test_normalize_jd_handles_empty_input(self):
        """Test handling of empty or None input."""
        assert normalize_jd("") == ""
        assert normalize_jd("   ") == ""
        assert normalize_jd(None) == ""
    
    def test_normalize_jd_preserves_plain_text(self):
        """Test that plain text without HTML is preserved correctly."""
        plain_text = """
        Software Engineer Position
        
        We are looking for an experienced developer.
        
        Requirements:
        - 5+ years of experience
        - Strong Python skills
        - Team collaboration
        """
        
        result = normalize_jd(plain_text)
        
        assert 'Software Engineer Position' in result
        assert 'experienced developer' in result
        assert '5+ years of experience' in result
        assert 'Strong Python skills' in result
        
        # Should still normalize whitespace
        lines = result.split('\n')
        # No line should have leading/trailing whitespace
        for line in lines:
            if line:  # Skip empty lines
                assert line == line.strip()
    
    def test_normalize_jd_deduplicates_identical_lines(self):
        """Test deduplication of identical lines while preserving order."""
        text_with_dupes = """
        Position: Software Engineer
        Requirements:
        - Python experience
        - JavaScript knowledge
        - Python experience
        - Team collaboration
        - JavaScript knowledge
        Benefits:
        - Health insurance
        - 401k matching
        """
        
        result = normalize_jd(text_with_dupes)
        
        # Each requirement should appear only once
        assert result.count('Python experience') == 1
        assert result.count('JavaScript knowledge') == 1
        assert result.count('Team collaboration') == 1
        
        # But different lines should be preserved
        assert 'Health insurance' in result
        assert '401k matching' in result


class TestGetCareerBrandDigest:
    """Test ChromaDB career brand query functionality."""
    
    @patch('app.services.fit_review.retrieval.get_chroma_client')
    @patch('app.services.fit_review.retrieval.get_embedding_function')
    def test_get_career_brand_digest_with_mocked_chroma(self, mock_embedding_fn, mock_client):
        """
        Test ChromaDB query with mocked client.
        
        Uses Chroma's documented contract for query() method to shape the mock.
        Verifies k limiting, threshold filtering, and digest concatenation.
        """
        # Setup mocks according to Chroma's documented API
        mock_collection = Mock()
        mock_collection.count.return_value = 10
        
        # Mock query results following Chroma's documented format
        mock_collection.query.return_value = {
            "documents": [[
                "Career growth opportunities in tech companies focus on...",
                "Professional development paths include mentorship and...", 
                "Leadership advancement requires strong technical skills...",
                "Work-life balance strategies for software engineers..."
            ]],
            "metadatas": [[
                {"doc_id": "career_001", "title": "Tech Career Growth"},
                {"doc_id": "career_002", "title": "Professional Development"},
                {"doc_id": "career_003", "title": "Leadership Skills"},
                {"doc_id": "career_004", "title": "Work-Life Balance"}
            ]],
            "distances": [0.1, 0.3, 0.5, 0.9]  # Cosine distances
        }
        
        mock_client_instance = Mock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        # Test with default parameters
        result = get_career_brand_digest(profile_id="test_user", k=3, threshold=0.2)
        
        # Verify ChromaDB API calls
        mock_client_instance.get_collection.assert_called_once_with(
            name="career_brand",
            embedding_function=mock_embedding_fn.return_value
        )
        
        # Query should include profile_id in search text
        mock_collection.query.assert_called_once()
        call_args = mock_collection.query.call_args
        assert "test_user" in call_args[1]["query_texts"][0]
        assert call_args[1]["n_results"] == 3  # k limiting
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "digest" in result
        assert "doc_ids" in result  
        assert "scores" in result
        assert "metadata" in result
        
        # Should filter by threshold (0.2)
        # Distances [0.1, 0.3, 0.5, 0.9] become similarities [0.9, 0.7, 0.5, 0.1]
        # Only [0.9, 0.7, 0.5] are >= 0.2 threshold
        assert len(result["doc_ids"]) == 3
        assert len(result["scores"]) == 3
        
        # Verify similarity score conversion (1 - distance)
        expected_scores = [0.9, 0.7, 0.5]  # 1 - [0.1, 0.3, 0.5]
        assert result["scores"] == expected_scores
        
        # Verify doc_ids extraction
        assert result["doc_ids"] == ["career_001", "career_002", "career_003"]
        
        # Digest should concatenate documents with separators
        assert len(result["digest"]) > 0
        assert "Career growth opportunities" in result["digest"]
        assert "|" in result["digest"]  # Separator should be present
    
    @patch('app.services.fit_review.retrieval.get_chroma_client')  
    def test_get_career_brand_digest_collection_not_found(self, mock_client):
        """Test graceful handling when career_brand collection doesn't exist."""
        mock_client_instance = Mock()
        mock_client_instance.get_collection.side_effect = Exception("Collection not found")
        mock_client.return_value = mock_client_instance
        
        result = get_career_brand_digest()
        
        # Should return empty digest with error metadata
        assert result["digest"] == ""
        assert result["doc_ids"] == []
        assert result["scores"] == []
        assert result["metadata"]["error"] == "Collection unavailable"
        assert result["metadata"]["signal"] == "insufficient"
    
    @patch('app.services.fit_review.retrieval.get_chroma_client')
    @patch('app.services.fit_review.retrieval.get_embedding_function')
    def test_get_career_brand_digest_empty_collection(self, mock_embedding_fn, mock_client):
        """Test handling of empty ChromaDB collection."""
        mock_collection = Mock()
        mock_collection.count.return_value = 0
        
        mock_client_instance = Mock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance
        
        result = get_career_brand_digest()
        
        # Should return empty digest with metadata indicating empty collection
        assert result["digest"] == ""
        assert result["doc_ids"] == []
        assert result["scores"] == []
        assert result["metadata"]["doc_count"] == 0
        assert result["metadata"]["signal"] == "insufficient"
    
    def test_get_career_brand_digest_respects_token_budget(self):
        """Test that digest respects ~2000 character budget."""
        with patch('app.services.fit_review.retrieval.get_chroma_client') as mock_client, \
             patch('app.services.fit_review.retrieval.get_embedding_function'):
            
            # Create long documents that would exceed budget
            long_doc = "x" * 1000  # 1000 char doc
            mock_collection = Mock()
            mock_collection.count.return_value = 5
            mock_collection.query.return_value = {
                "documents": [[long_doc, long_doc, long_doc, long_doc, long_doc]],
                "metadatas": [[{"doc_id": f"doc_{i}"} for i in range(5)]],
                "distances": [0.1, 0.1, 0.1, 0.1, 0.1]
            }
            
            mock_client_instance = Mock()
            mock_client_instance.get_collection.return_value = mock_collection
            mock_client.return_value = mock_client_instance
            
            result = get_career_brand_digest()
            
            # Digest should be limited to reasonable size (budget ~2000 chars)
            assert len(result["digest"]) <= 2000
            assert len(result["digest"]) > 0


class TestBuildContext:
    """Test context building orchestration."""
    
    @patch('app.services.fit_review.retrieval.get_career_brand_digest')
    def test_build_context_returns_expected_keys(self, mock_career_digest):
        """Test that build_context returns all expected keys for YAML crews."""
        # Mock career brand digest response
        mock_career_digest.return_value = {
            "digest": "Sample career insights...",
            "doc_ids": ["doc_1", "doc_2"], 
            "scores": [0.8, 0.6],
            "metadata": {"signal": "sufficient", "retrieved": 2}
        }
        
        # Sample job posting
        job_posting = {
            "title": "Senior AI Engineer",
            "company": "TechCorp",
            "description": "<p>We need a <strong>senior AI engineer</strong> with Python experience.</p>",
            "location": "San Francisco, CA"
        }
        
        result = build_context(job_posting, profile_id="test_user")
        
        # Verify all expected keys are present
        required_keys = ["normalized_jd", "doc_ids", "scores", "tags", "metadata"]
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        # Verify types and basic content
        assert isinstance(result["normalized_jd"], str)
        assert isinstance(result["doc_ids"], list)
        assert isinstance(result["scores"], list)
        assert isinstance(result["tags"], list)
        assert isinstance(result["metadata"], dict)
        
        # Normalized JD should have HTML removed
        assert "<p>" not in result["normalized_jd"]
        assert "<strong>" not in result["normalized_jd"]
        assert "senior AI engineer" in result["normalized_jd"]
        
        # Career data should be passed through
        assert result["doc_ids"] == ["doc_1", "doc_2"]
        assert result["scores"] == [0.8, 0.6]
        
        # Tags should be extracted
        assert "ai" in result["tags"]  # From title
        assert "senior" in result["tags"]  # From title
        
        # Metadata should include length info
        assert "original_jd_length" in result["metadata"]
        assert "normalized_jd_length" in result["metadata"]
        assert result["metadata"]["original_jd_length"] > 0
    
    def test_build_context_handles_missing_description(self):
        """Test handling of job posting without description."""
        job_posting = {
            "title": "Python Developer",
            "company": "StartupCorp"
            # Missing description
        }
        
        with patch('app.services.fit_review.retrieval.get_career_brand_digest') as mock_career:
            mock_career.return_value = {
                "digest": "", "doc_ids": [], "scores": [], 
                "metadata": {"signal": "insufficient"}
            }
            
            result = build_context(job_posting)
            
            # Should handle gracefully
            assert result["normalized_jd"] == ""
            assert result["metadata"]["original_jd_length"] == 0
            assert result["metadata"]["normalized_jd_length"] == 0


class TestExtractTags:
    """Test tag extraction functionality."""
    
    def test_extract_tags_domain_detection(self):
        """Test domain tag extraction from job content."""
        job_posting = {
            "title": "Senior AI/ML Engineer",
            "description": "Work with machine learning models and React frontend"
        }
        
        tags = _extract_tags(job_posting)
        
        # Should detect AI/ML and frontend domains
        assert "ai" in tags
        assert "frontend" in tags
        
        # Should detect seniority
        assert "senior" in tags
        
        # Should not detect unrelated domains
        assert "mobile" not in tags
    
    def test_extract_tags_seniority_detection(self):
        """Test seniority level extraction."""
        test_cases = [
            ("Junior Developer", ["entry"]),
            ("Senior Software Engineer", ["senior"]),
            ("Staff Platform Engineer", ["staff", "platform"]),
            ("Principal Architect", ["staff"]),
            ("Engineering Manager", ["executive"])
        ]
        
        for title, expected_seniority_tags in test_cases:
            job_posting = {"title": title, "description": ""}
            tags = _extract_tags(job_posting)
            
            # Check that at least one expected seniority tag is present
            seniority_found = any(tag in tags for tag in expected_seniority_tags if tag in ["entry", "mid", "senior", "staff", "executive"])
            assert seniority_found, f"No seniority tag found in {tags} for title '{title}'"
    
    def test_extract_tags_deterministic_output(self):
        """Test that tag extraction is deterministic and sorted."""
        job_posting = {
            "title": "Senior Data Science Engineer",
            "description": "Python and machine learning experience"
        }
        
        # Run multiple times to ensure consistency
        tags1 = _extract_tags(job_posting)
        tags2 = _extract_tags(job_posting)
        tags3 = _extract_tags(job_posting)
        
        assert tags1 == tags2 == tags3
        
        # Should be sorted
        assert tags1 == sorted(tags1)
        
        # Should contain expected tags
        assert "ai" in tags1  # From "machine learning"
        assert "data" in tags1  # From "Data Science"
        assert "senior" in tags1  # From "Senior"
    
    def test_extract_tags_multiple_domains(self):
        """Test extraction when multiple domains are present."""
        job_posting = {
            "title": "Full Stack Engineer",
            "description": "React frontend, Python backend, AWS cloud infrastructure, mobile app development"
        }
        
        tags = _extract_tags(job_posting)
        
        # Should detect multiple domains
        expected_domains = ["frontend", "backend", "platform", "mobile"]
        for domain in expected_domains:
            assert domain in tags, f"Expected domain '{domain}' not found in {tags}"