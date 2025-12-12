import sys
from unittest.mock import MagicMock

# Mock dependencies before import
sys.modules["loguru"] = MagicMock()
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.errors"] = MagicMock()
sys.modules["app.services.infrastructure"] = MagicMock()
sys.modules["app.services.embeddings"] = MagicMock()
sys.modules["app.core.config"] = MagicMock()
sys.modules["app.schemas.chroma"] = MagicMock()

import unittest
# Now import the service
# We need to make sure we can import it even if other local imports fail
# The prompt implies we are in python-service root.
# app.services.chroma_service imports from .infrastructure etc.

from app.services.chroma_service import ChromaService

class TestChunkDedup(unittest.TestCase):
    def setUp(self):
        # We need to mock get_settings inside ChromaService init if it's called
        # The __init__ calls get_settings()
        
        # Patching get_settings
        with unittest.mock.patch('app.services.chroma_service.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock()
            self.service = ChromaService()

    def test_deduplicate_chunks_no_overlap(self):
        chunks = ["Hello world ", "This is a test"]
        # Should just concat
        result = self.service._deduplicate_chunks(chunks)
        self.assertEqual(result, "Hello world This is a test")

    def test_deduplicate_chunks_simple_overlap(self):
        # Overlap is " overlap."
        chunks = ["This is a chunk with overlap.", " overlap. And this is the rest."]
        result = self.service._deduplicate_chunks(chunks)
        self.assertEqual(result, "This is a chunk with overlap. And this is the rest.")

    def test_deduplicate_chunks_chunk_text_roundtrip(self):
        # Simulate the actual splitting process
        text = "This is a long text that will be split into chunks and then reconstructed. We want to ensure that the reconstruction is perfect and no text is duplicated or lost during the process."
        
        # Manually create overlapping chunks similar to _chunk_text
        # Let's say we split every 10 words with 3 words overlap
        words = text.split()
        chunks = []
        chunk_size = 10
        overlap = 3
        
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start = max(0, end - overlap)
            
        print(f"Chunks: {chunks}")
        
        result = self.service._deduplicate_chunks(chunks)
        self.assertEqual(result, text)

    def test_deduplicate_chunks_empty(self):
        self.assertEqual(self.service._deduplicate_chunks([]), "")

    def test_deduplicate_chunks_single(self):
        self.assertEqual(self.service._deduplicate_chunks(["Single chunk"]), "Single chunk")

if __name__ == '__main__':
    unittest.main()
