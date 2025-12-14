from python_service.app.services.infrastructure.chroma import get_chroma_client

client = get_chroma_client()
try:
    client.delete_collection("career_brand")
    print("✅ Successfully deleted career_brand collection")
except Exception as e:
    print(f"❌ Failed to delete collection: {e}")

# List remaining collections
try:
    collections = client.list_collections()
    print(f"Remaining collections: {[c.name for c in collections]}")
except Exception as e:
    print(f"Failed to list collections: {e}")
