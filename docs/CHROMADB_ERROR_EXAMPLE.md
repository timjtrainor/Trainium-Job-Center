# ChromaDB Error Handling Example

## Before the improvements:
```json
{
  "success": false,
  "message": "Embedding model mismatch: collection uses 'sentence_transformer:BAAI/bge-m3' but settings specify 'openai:text-embedding-3-small'. Delete or recreate the collection.",
  "collection_name": "my_documents",
  "document_id": "",
  "chunks_created": 0
}
```

## After the improvements:
```json
{
  "success": false,
  "message": "Embedding model mismatch detected!\nCollection 'my_documents' was created with: sentence_transformer:BAAI/bge-m3\nCurrent configuration expects: openai:text-embedding-3-small\n\nThis happens when you change embedding providers or models after creating collections.\nSolutions:\n1. Delete the collection and recreate it: DELETE /chroma/collections/my_documents\n2. Or change your .env back to: EMBEDDING_PROVIDER=sentence_transformer, EMBEDDING_MODEL=BAAI/bge-m3\n3. Or use a different collection name for the new embedding model",
  "collection_name": "my_documents",
  "document_id": "",
  "chunks_created": 0,
  "error_type": "EMBEDDING_MISMATCH",
  "suggestions": [
    "Delete collection: DELETE /chroma/collections/my_documents",
    "Use a different collection name",
    "Revert .env to previous embedding settings"
  ]
}
```

## Key Improvements:
1. **Detailed explanation** of what went wrong and why
2. **Specific error type** for programmatic handling
3. **Actionable suggestions** array for UI display
4. **Step-by-step solutions** in the message
5. **Better logging** with full context and tracebacks

This makes it much easier for users to understand and resolve ChromaDB upload issues!