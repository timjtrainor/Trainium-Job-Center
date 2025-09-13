from crewai_tools import tool
import chromadb
import os


@tool("Chroma Search")
def chroma_search(query: str) -> str:
    """
    Search the ChromaDB vector database for relevant documents based on a query.
    """
    chroma_host = os.getenv("CHROMA_URL", "chromadb")
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))

    client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
    collection = client.get_or_create_collection("career_brand_framework")

    results = collection.query(query_texts=[query], n_results=5)
    docs = results.get("documents", [[]])[0]

    return "\n".join(docs) if docs else "No relevant documents found."