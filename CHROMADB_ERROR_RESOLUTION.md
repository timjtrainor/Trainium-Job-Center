# ChromaDB Upload Error Resolution Guide

This guide helps resolve common ChromaDB upload errors, especially when changing embedding providers or models.

## Common Error: Embedding Model Mismatch

### Problem
When you change embedding providers (e.g., from `sentence_transformer` to `openai`) or models (e.g., from `BAAI/bge-m3` to `text-embedding-3-small`) in your `.env` file, existing ChromaDB collections will have a mismatch error.

### Error Message Example
```
Embedding model mismatch detected!
Collection 'my_collection' was created with: sentence_transformer:BAAI/bge-m3
Current configuration expects: openai:text-embedding-3-small

This happens when you change embedding providers or models after creating collections.
```

### Solutions

#### Option 1: Delete and Recreate Collection (Recommended)
```bash
# Delete the problematic collection via API
curl -X DELETE http://localhost:8000/chroma/collections/my_collection

# Or use the UI to delete the collection
# Then upload your files again
```

#### Option 2: Use a Different Collection Name
When uploading files, use a new collection name like:
- `documents_openai` instead of `documents`
- `knowledge_base_v2` instead of `knowledge_base`

#### Option 3: Revert Environment Configuration
Edit your `.env` file to match the existing collection:
```bash
EMBEDDING_PROVIDER=sentence_transformer
EMBEDDING_MODEL=BAAI/bge-m3
```

## Understanding Error Types

The system now provides specific error types to help identify issues:

### `EMBEDDING_MISMATCH`
- **Cause**: Collection was created with different embedding model
- **Solution**: Delete collection or use different name

### `CHROMADB_ERROR`
- **Cause**: ChromaDB service issues or configuration problems
- **Solutions**: 
  - Check if ChromaDB service is running
  - Verify `CHROMA_URL` and `CHROMA_PORT` in `.env`
  - Restart ChromaDB service

### `CONNECTION_ERROR`
- **Cause**: Cannot connect to ChromaDB service
- **Solutions**:
  - Ensure `docker-compose up chromadb` is running
  - Check network connectivity
  - Verify Docker services are healthy

### `SYSTEM_ERROR`
- **Cause**: Unexpected system error
- **Solutions**:
  - Check application logs
  - Verify system resources
  - Contact administrator

## Environment Configuration

### For OpenAI Embeddings
```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your_actual_api_key_here
```

### For SentenceTransformer Embeddings
```bash
EMBEDDING_PROVIDER=sentence_transformer
EMBEDDING_MODEL=BAAI/bge-m3
```

## Checking Current Collections

List existing collections to see their embedding configurations:
```bash
curl http://localhost:8000/chroma/collections
```

## Logs and Debugging

The system now provides detailed logging for troubleshooting:

1. **Application Logs**: Check Python service logs for detailed error information
2. **Error Responses**: API responses include actionable suggestions
3. **Traceback Information**: Full error tracebacks are logged for debugging

## Best Practices

1. **Plan Embedding Changes**: Decide on embedding provider before creating collections
2. **Use Descriptive Collection Names**: Include provider/model in the name (e.g., `docs_openai`, `knowledge_bge`)
3. **Backup Important Collections**: Export data before making configuration changes
4. **Test Configuration**: Upload a small test file when changing embedding settings

## Getting Help

If you continue experiencing issues:

1. Check the application logs for detailed error information
2. Verify your `.env` configuration matches your intended setup
3. Ensure all required API keys are properly set
4. Try uploading to a new collection with a unique name

The error messages now include specific suggestions tailored to your situation, making it easier to resolve issues quickly.