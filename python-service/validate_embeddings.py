#!/usr/bin/env python3
"""Validation script for embedding service configuration."""

import os
import sys
import asyncio
from unittest.mock import MagicMock

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_sentence_transformer_config():
    """Test SentenceTransformer embedding configuration."""
    # Mock the dependencies to avoid requiring actual packages
    sys.modules['chromadb.utils.embedding_functions'] = MagicMock()
    sys.modules['loguru'] = MagicMock()
    
    # Set environment for SentenceTransformer
    os.environ['EMBEDDING_PROVIDER'] = 'sentence_transformer'
    os.environ['EMBEDDING_MODEL'] = 'BAAI/bge-m3'
    
    try:
        from app.services.embeddings.factory import create_embedding_function
        
        # Mock the embedding functions module
        import chromadb.utils.embedding_functions as ef
        mock_st_func = MagicMock()
        ef.SentenceTransformerEmbeddingFunction = MagicMock(return_value=mock_st_func)
        
        result = create_embedding_function('sentence_transformer', 'BAAI/bge-m3')
        
        ef.SentenceTransformerEmbeddingFunction.assert_called_once_with(
            model_name='BAAI/bge-m3',
            normalize_embeddings=True,
            device='cpu'
        )
        
        print("✓ SentenceTransformer embedding configuration works")
        return True
        
    except Exception as e:
        print(f"✗ SentenceTransformer configuration failed: {e}")
        return False

def test_openai_config():
    """Test OpenAI embedding configuration."""
    # Set environment for OpenAI
    os.environ['EMBEDDING_PROVIDER'] = 'openai'
    os.environ['EMBEDDING_MODEL'] = 'text-embedding-3-small'
    os.environ['OPENAI_API_KEY'] = 'test-key'
    
    try:
        from app.services.embeddings.factory import create_embedding_function
        
        # Mock the openai module and embedding functions
        sys.modules['openai'] = True  # Mock package existence
        import chromadb.utils.embedding_functions as ef
        mock_openai_func = MagicMock()
        ef.OpenAIEmbeddingFunction = MagicMock(return_value=mock_openai_func)
        
        result = create_embedding_function('openai', 'text-embedding-3-small')
        
        ef.OpenAIEmbeddingFunction.assert_called_once_with(
            api_key='test-key',
            model_name='text-embedding-3-small'
        )
        
        print("✓ OpenAI embedding configuration works")
        return True
        
    except Exception as e:
        print(f"✗ OpenAI configuration failed: {e}")
        return False

def test_config_integration():
    """Test configuration integration with settings."""
    try:
        # Mock all the dependencies
        sys.modules['dotenv'] = MagicMock()
        sys.modules['chromadb'] = MagicMock()
        
        from app.core.config import Settings
        
        # Test default settings
        settings = Settings()
        assert settings.embedding_provider == 'sentence_transformer'
        assert settings.embedding_model == 'BAAI/bge-m3'
        
        print("✓ Configuration integration works")
        return True
        
    except Exception as e:
        print(f"✗ Configuration integration failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("Validating embedding service configuration...")
    print()
    
    tests = [
        test_config_integration,
        test_sentence_transformer_config,
        test_openai_config,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print()
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} tests passed!")
        return 0
    else:
        print(f"❌ {passed}/{total} tests passed")
        return 1

if __name__ == '__main__':
    sys.exit(main())