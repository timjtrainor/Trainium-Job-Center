
import chromadb
import os

def inspect_metadata():
    print("Connecting to ChromaDB...")
    try:
        # Try connecting to localhost:8001 (default from .env)
        client = chromadb.HttpClient(host='localhost', port=8001)
        
        print("Listing collections...")
        collections = client.list_collections()
        print(f"Collections: {[c.name for c in collections]}")
        
        if "proof_points" not in [c.name for c in collections]:
            print("Collection 'proof_points' not found.")
            return

        collection = client.get_collection("proof_points")
        
        # Get all items
        result = collection.get(include=["metadatas"])
        
        if not result["ids"]:
            print("No documents found in 'proof_points' collection.")
            return

        print(f"Found {len(result['ids'])} chunks.")
        
        # Group by doc_id to see unique documents
        seen_docs = set()
        for i, metadata in enumerate(result["metadatas"]):
            doc_id = metadata.get("doc_id", "unknown")
            if doc_id not in seen_docs:
                print(f"\nDocument ID: {doc_id}")
                print(f"Metadata: {metadata}")
                seen_docs.add(doc_id)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_metadata()
