from crewai.tools import BaseTool
from typing import Optional
import os

from ...infrastructure.chroma import get_chroma_client


class ChromaSearchTool(BaseTool):
    """Tool for performing similarity search using ChromaDB.
    
    Note: This tool uses existing collections and inherits their embedding functions.
    New collections should be created via ChromaService which uses configurable embeddings.
    """

    name: str = "chroma_search"
    description: str = (
        "Searches a ChromaDB collection for documents similar to the input query."
    )

    collection_name: Optional[str] = None
    n_results: int = 4

    def _run(self, query: str) -> str:
        collection = self.collection_name or os.getenv("CHROMA_COLLECTION", "default")
        try:
            client = get_chroma_client()
            chroma_collection = client.get_or_create_collection(collection)
            results = chroma_collection.query(
                query_texts=[query], n_results=self.n_results
            )
            documents = results.get("documents", [])
            if documents and documents[0]:
                return "\n".join(documents[0])
            return "No results found."
        except Exception as e:  # pragma: no cover - best effort error message
            return f"Error executing Chroma search: {e}"
