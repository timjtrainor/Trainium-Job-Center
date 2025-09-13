"""ChromaDB search tool for CrewAI."""

import chromadb
from crewai.tools import BaseTool


def get_chroma_client() -> chromadb.Client:
    """Return a ChromaDB HTTP client using environment configuration."""
    import os

    chroma_host = os.getenv("CHROMA_URL", "chromadb")
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
    return chromadb.HttpClient(host=chroma_host, port=chroma_port)


class ChromaSearchTool(BaseTool):
    """Search a ChromaDB collection for relevant documents."""

    name: str = "chroma_search"
    description: str = (
        "Searches a ChromaDB collection for documents similar to the query."
    )

    collection_name: str
    n_results: int = 5

    def _run(self, query: str) -> str:
        client = get_chroma_client()
        collection = client.get_or_create_collection(self.collection_name)
        results = collection.query(query_texts=[query], n_results=self.n_results)
        docs = results.get("documents", [[]])[0]
        return "\n".join(docs) if docs else "No relevant documents found."


__all__ = ["ChromaSearchTool", "get_chroma_client"]

