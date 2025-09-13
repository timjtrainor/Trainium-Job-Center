"""ChromaDB search tools for CrewAI following 0.186.1 best practices."""

from typing import List, Optional, Dict, Any
from crewai_tools import tool
from ...infrastructure.chroma import get_chroma_client


@tool
def chroma_search(query: str, collection_name: str = "documents", n_results: int = 5) -> str:
    """
    Search for relevant documents in a ChromaDB collection.
    
    This tool searches a specified ChromaDB collection for documents that are semantically 
    similar to the provided query. It returns the most relevant document chunks that can
    be used for research, analysis, or decision making.
    
    Args:
        query (str): The search query to find relevant documents
        collection_name (str): Name of the ChromaDB collection to search (default: "documents")
        n_results (int): Maximum number of results to return (default: 5)
    
    Returns:
        str: A formatted string containing the most relevant document content, 
             or a message if no relevant documents are found
    
    Example:
        result = chroma_search("machine learning job requirements", "job_postings", 3)
    """
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(collection_name)
        
        results = collection.query(
            query_texts=[query], 
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        if not documents:
            return f"No relevant documents found in collection '{collection_name}' for query: '{query}'"
        
        # Format results with metadata for better context
        formatted_results = []
        for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances), 1):
            result_text = f"--- Result {i} ---\n"
            if metadata and isinstance(metadata, dict):
                # Add relevant metadata if available
                if "title" in metadata:
                    result_text += f"Title: {metadata['title']}\n"
                if "source" in metadata:
                    result_text += f"Source: {metadata['source']}\n"
                result_text += f"Relevance: {1 - distance:.3f}\n"
            result_text += f"Content: {doc}\n"
            formatted_results.append(result_text)
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching ChromaDB collection '{collection_name}': {str(e)}"


@tool
def chroma_list_collections() -> str:
    """
    List all available ChromaDB collections and their document counts.
    
    This tool provides crews with visibility into what collections are available
    for document search and review. It helps agents understand what data sources
    they can access for their analysis.
    
    Returns:
        str: A formatted list of collection names with document counts and metadata
    
    Example:
        collections = chroma_list_collections()
    """
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        
        if not collections:
            return "No collections found in ChromaDB. No documents are currently available for search."
        
        collection_info = []
        collection_info.append("Available ChromaDB Collections:\n" + "="*40)
        
        for collection in collections:
            try:
                # Get collection details
                col_obj = client.get_collection(collection.name)
                count = col_obj.count()
                metadata = getattr(collection, 'metadata', {}) or {}
                
                info = f"Collection: {collection.name}\n"
                info += f"Documents: {count}\n"
                
                if metadata:
                    info += "Metadata:\n"
                    for key, value in metadata.items():
                        info += f"  {key}: {value}\n"
                
                collection_info.append(info)
                
            except Exception as e:
                collection_info.append(f"Collection: {collection.name}\nError retrieving details: {str(e)}\n")
        
        return "\n".join(collection_info)
        
    except Exception as e:
        return f"Error listing ChromaDB collections: {str(e)}"


@tool  
def chroma_search_across_collections(query: str, collections: Optional[List[str]] = None, n_results: int = 3) -> str:
    """
    Search for documents across multiple ChromaDB collections.
    
    This tool allows comprehensive document review by searching across multiple collections
    simultaneously. It's useful when you need to find relevant information that might be
    stored in different collections (e.g., job postings, company info, interview feedback).
    
    Args:
        query (str): The search query to find relevant documents
        collections (List[str], optional): List of collection names to search. 
                                         If None, searches all available collections
        n_results (int): Maximum number of results to return per collection (default: 3)
    
    Returns:
        str: Formatted results from all searched collections with collection labels
    
    Example:
        result = chroma_search_across_collections(
            "python developer requirements", 
            ["job_postings", "company_profiles"], 
            2
        )
    """
    try:
        client = get_chroma_client()
        
        # Get target collections
        if collections is None:
            # Search all collections
            all_collections = client.list_collections()
            target_collections = [col.name for col in all_collections]
        else:
            target_collections = collections
        
        if not target_collections:
            return "No collections available to search."
        
        all_results = []
        all_results.append(f"Cross-Collection Search Results for: '{query}'\n" + "="*60)
        
        for collection_name in target_collections:
            try:
                collection = client.get_collection(collection_name)
                count = collection.count()
                
                if count == 0:
                    all_results.append(f"\n[{collection_name}] - Empty collection, skipping")
                    continue
                
                results = collection.query(
                    query_texts=[query], 
                    n_results=n_results,
                    include=["documents", "metadatas", "distances"]
                )
                
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0] 
                distances = results.get("distances", [[]])[0]
                
                if documents:
                    all_results.append(f"\n[{collection_name}] - Found {len(documents)} results:")
                    
                    for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances), 1):
                        result_text = f"  {i}. (Relevance: {1 - distance:.3f})"
                        if metadata and isinstance(metadata, dict) and "title" in metadata:
                            result_text += f" {metadata['title']}"
                        result_text += f"\n     {doc[:200]}{'...' if len(doc) > 200 else ''}"
                        all_results.append(result_text)
                else:
                    all_results.append(f"\n[{collection_name}] - No relevant results found")
                    
            except Exception as e:
                all_results.append(f"\n[{collection_name}] - Error: {str(e)}")
        
        return "\n".join(all_results)
        
    except Exception as e:
        return f"Error performing cross-collection search: {str(e)}"


# Legacy support - maintain backward compatibility
class ChromaSearchTool:
    """Legacy ChromaSearchTool class for backward compatibility."""
    
    def __init__(self, collection_name: str = "documents", n_results: int = 5):
        self.collection_name = collection_name
        self.n_results = n_results
        self.name = "chroma_search"
        self.description = "Searches a ChromaDB collection for documents similar to the query."
    
    def run(self, query: str) -> str:
        """Legacy run method for backward compatibility."""
        return chroma_search(query, self.collection_name, self.n_results)
    
    def _run(self, query: str) -> str:
        """Legacy _run method for backward compatibility."""
        return self.run(query)


# Export all tools and legacy classes
__all__ = [
    "chroma_search",
    "chroma_list_collections", 
    "chroma_search_across_collections",
    "ChromaSearchTool",
]

