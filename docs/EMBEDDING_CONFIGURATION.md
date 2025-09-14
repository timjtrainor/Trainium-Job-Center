# Embedding Service Configuration

The Trainium Job Center Python service now supports configurable embedding services for ChromaDB integration. You can choose between different embedding providers to suit your needs.

## Supported Embedding Providers

### 1. SentenceTransformer (Default)
- **Provider**: `sentence_transformer`
- **Default Model**: `BAAI/bge-m3`
- **Description**: Uses local SentenceTransformer models for generating embeddings
- **Requirements**: sentence-transformers package (included in requirements.txt)

### 2. OpenAI Embeddings
- **Provider**: `openai`
- **Recommended Model**: `text-embedding-3-small`
- **Description**: Uses OpenAI's embedding API for generating embeddings
- **Requirements**: OpenAI API key and openai package (included in requirements.txt)

## Configuration

Set the following environment variables to configure your embedding service:

```bash
# Embedding provider (sentence_transformer or openai)
EMBEDDING_PROVIDER=sentence_transformer

# Embedding model name
EMBEDDING_MODEL=BAAI/bge-m3

# For OpenAI embeddings, also set:
OPENAI_API_KEY=your_openai_api_key_here
```

## Example Configurations

### Using SentenceTransformer (Default)
```bash
EMBEDDING_PROVIDER=sentence_transformer
EMBEDDING_MODEL=BAAI/bge-m3
```

### Using OpenAI text-embedding-3-small
```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-your-key-here
```

### Using OpenAI text-embedding-ada-002
```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_API_KEY=sk-your-key-here
```

## Migration from Existing Setup

If you have existing ChromaDB collections created with the previous hardcoded SentenceTransformer embeddings, they will continue to work. New collections will use the configured embedding service.

**Note**: Collections created with different embedding functions are not compatible with each other. If you change embedding providers, you may need to recreate your collections.

## Performance Considerations

- **SentenceTransformer**: Runs locally, no API costs, but requires compute resources
- **OpenAI**: Runs in the cloud, has API costs, but offloads compute

## Code Usage

The embedding configuration is automatically applied throughout the system:

- `ChromaService` uses the configured embeddings for new collections
- `ChromaSearchTool` works with existing collections regardless of their embedding function
- Data loading scripts use the configured embeddings

No code changes are required - just set the environment variables and restart the service.