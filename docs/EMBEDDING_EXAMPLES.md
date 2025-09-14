# Example: Switching Between Embedding Services

This example demonstrates how to configure the Trainium Job Center to use different embedding services.

## Default Configuration (SentenceTransformer)

```bash
# .env file or environment variables
EMBEDDING_PROVIDER=sentence_transformer
EMBEDDING_MODEL=BAAI/bge-m3
```

With this configuration, ChromaDB will use the local SentenceTransformer model for embeddings.

## OpenAI Configuration

```bash
# .env file or environment variables
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-your-openai-api-key-here
```

With this configuration, ChromaDB will use OpenAI's text-embedding-3-small model.

## Usage in Code

The configuration is automatically picked up by all ChromaDB operations:

```python
from app.services.chroma_service import ChromaService
from app.schemas.chroma import ChromaUploadRequest

# Create service instance
service = ChromaService()

# Upload document - uses configured embedding service
request = ChromaUploadRequest(
    collection_name="my_documents",
    title="Example Document",
    tags=["example"],
    document_text="This document will be embedded using the configured service."
)

result = await service.upload_document(request)
```

## Available Models

### SentenceTransformer Models
- `BAAI/bge-m3` (default)
- `all-MiniLM-L6-v2`
- `all-mpnet-base-v2`
- Any model supported by sentence-transformers

### OpenAI Models
- `text-embedding-3-small` (recommended)
- `text-embedding-3-large`
- `text-embedding-ada-002`

## Performance Comparison

| Provider | Speed | Cost | Quality | Resource Usage |
|----------|-------|------|---------|----------------|
| SentenceTransformer | Fast | Free | Good | Local CPU/GPU |
| OpenAI | Variable | $$$$ | Excellent | API calls |

Choose based on your requirements for cost, performance, and quality.