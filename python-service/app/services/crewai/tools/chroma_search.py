"""Enhanced ChromaDB search tools for CrewAI following 0.186.1 best practices."""

from typing import List, Optional, Dict, Any
import asyncio
from crewai.tools import tool
from ...infrastructure.chroma import get_chroma_client
from ...chroma_manager import get_chroma_manager, CollectionType


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
        # Use the enhanced manager for better error handling and collection management
        manager = get_chroma_manager()
        
        # Run async search in sync context
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            manager.search_collection(collection_name, query, n_results)
        )
        
        if not result["success"]:
            return f"Error searching collection '{collection_name}': {result.get('error', 'Unknown error')}"
        
        documents = result["documents"]
        metadatas = result["metadatas"]
        distances = result["distances"]
        
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
                if "company" in metadata:
                    result_text += f"Company: {metadata['company']}\n"
                if "collection_type" in metadata:
                    result_text += f"Type: {metadata['collection_type']}\n"
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
        manager = get_chroma_manager()
        
        # Run async list in sync context
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        collections = loop.run_until_complete(manager.list_all_collections())
        
        if not collections:
            return "No collections found in ChromaDB. No documents are currently available for search."
        
        collection_info = []
        collection_info.append("Available ChromaDB Collections:\n" + "="*50)
        
        for collection in collections:
            info = f"Collection: {collection.name}\n"
            info += f"Documents: {collection.count}\n"
            
            if collection.metadata:
                metadata = collection.metadata
                if "collection_type" in metadata:
                    info += f"Type: {metadata['collection_type']}\n"
                if "description" in metadata:
                    info += f"Description: {metadata['description']}\n"
                if "embed_model" in metadata:
                    info += f"Embedding Model: {metadata['embed_model']}\n"
                if "created_at" in metadata:
                    info += f"Created: {metadata['created_at']}\n"
            
            collection_info.append(info)
        
        # Add information about registered collection types
        registered_configs = manager.list_registered_collections()
        if registered_configs:
            collection_info.append("\nSupported Collection Types:")
            collection_info.append("-" * 30)
            for config in registered_configs:
                type_info = f"• {config.name} ({config.collection_type.value}): {config.description}"
                collection_info.append(type_info)
        
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
        manager = get_chroma_manager()
        
        # Run async search in sync context
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            manager.search_across_collections(query, collections, n_results)
        )
        
        if not result["success"]:
            return f"Error performing cross-collection search: {result.get('error', 'Unknown error')}"
        
        collections_searched = result["collections_searched"]
        results = result["results"]
        
        if not collections_searched:
            return "No collections available to search."
        
        all_results = []
        all_results.append(f"Cross-Collection Search Results for: '{query}'\n" + "="*60)
        
        for collection_name in collections_searched:
            collection_result = results.get(collection_name, {})
            
            if not collection_result.get("success", False):
                all_results.append(f"\n[{collection_name}] - Error: {collection_result.get('error', 'Unknown error')}")
                continue
            
            documents = collection_result.get("documents", [])
            metadatas = collection_result.get("metadatas", [])
            distances = collection_result.get("distances", [])
            
            if not documents:
                all_results.append(f"\n[{collection_name}] - No relevant results found")
                continue
            
            all_results.append(f"\n[{collection_name}] - Found {len(documents)} results:")
            
            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances), 1):
                result_text = f"  {i}. (Relevance: {1 - distance:.3f})"
                if metadata and isinstance(metadata, dict):
                    if "title" in metadata:
                        result_text += f" {metadata['title']}"
                    if "company" in metadata:
                        result_text += f" - {metadata['company']}"
                result_text += f"\n     {doc[:200]}{'...' if len(doc) > 200 else ''}"
                all_results.append(result_text)
        
        return "\n".join(all_results)
        
    except Exception as e:
        return f"Error performing cross-collection search: {str(e)}"


@tool
def search_job_postings(query: str, n_results: int = 5) -> str:
    """
    Search specifically for job posting documents.
    
    Specialized tool for searching job postings with optimized parameters
    for job-related content analysis.
    
    Args:
        query (str): Job-related search query (skills, role, company, etc.)
        n_results (int): Maximum number of job postings to return (default: 5)
    
    Returns:
        str: Formatted job posting search results
    """
    return chroma_search(query, "job_postings", n_results)


@tool
def search_company_profiles(query: str, n_results: int = 5) -> str:
    """
    Search specifically for company profile documents.
    
    Specialized tool for searching company information, culture, and organizational data.
    
    Args:
        query (str): Company-related search query (culture, values, benefits, etc.)
        n_results (int): Maximum number of company profiles to return (default: 5)
    
    Returns:
        str: Formatted company profile search results
    """
    return chroma_search(query, "company_profiles", n_results)


@tool
def search_career_brands(query: str, n_results: int = 5) -> str:
    """
    Search specifically for career branding documents.
    
    Specialized tool for searching personal career branding and positioning content.
    
    Args:
        query (str): Career branding search query (skills, experience, positioning, etc.)
        n_results (int): Maximum number of career brand documents to return (default: 5)
    
    Returns:
        str: Formatted career branding search results
    """
    return chroma_search(query, "career_brand", n_results)


@tool
def search_career_paths(query: str, n_results: int = 5) -> str:
    """
    Search specifically for career path documents.

    Specialized tool for searching personal career paths  content.

    Args:
        query (str): Career paths search query (skills, experience, positioning, etc.)
        n_results (int): Maximum number of career paths documents to return (default: 5)

    Returns:
        str: Formatted career paths search results
    """
    return chroma_search(query, "career_paths", n_results)


@tool
def search_job_search_strategies(query: str, n_results: int = 5) -> str:
    """
    Search specifically for job search strategy documents.

    Specialized tool for searching job search strategy documents.

    Args:
        query (str): Job search strategy query (skills, experience, positioning, etc.)
        n_results (int): Maximum number of job search strategy documents to return (default: 5)

    Returns:
        str: Formatted career paths search results
    """
    return chroma_search(query, "job_search_strategies", n_results)

@tool
def contextual_job_analysis(job_title: str, company_name: str = "", skills: str = "", n_results: int = 3) -> str:
    """
    Perform contextual analysis of job opportunities using multiple data sources.
    
    This tool searches across job postings and company profiles to provide
    comprehensive context for job analysis and decision making.
    
    Args:
        job_title (str): The job title or role to analyze
        company_name (str): Optional company name for targeted analysis
        skills (str): Optional comma-separated skills to focus on
        n_results (int): Number of results per collection (default: 3)
    
    Returns:
        str: Comprehensive contextual analysis combining multiple data sources
    """
    try:
        # Build comprehensive search query
        query_parts = [job_title]
        if company_name:
            query_parts.append(company_name)
        if skills:
            query_parts.append(skills)
        
        main_query = " ".join(query_parts)
        
        # Search relevant collections
        collections_to_search = ["job_postings"]
        if company_name:
            collections_to_search.append("company_profiles")
        
        # Get contextual information
        context_result = chroma_search_across_collections(
            main_query, collections_to_search, n_results
        )
        
        # Add career branding context if available
        career_context = search_career_brands(job_title, 2)
        
        analysis = [
            f"Contextual Job Analysis for: {job_title}",
            "=" * 60,
            "\n📋 JOB MARKET CONTEXT:",
            context_result,
        ]
        
        if "No relevant documents found" not in career_context:
            analysis.extend([
                "\n🎯 CAREER POSITIONING CONTEXT:",
                career_context
            ])
        
        return "\n".join(analysis)
        
    except Exception as e:
        return f"Error performing contextual job analysis: {str(e)}"


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
    "search_job_postings",
    "search_company_profiles", 
    "search_career_brands",
    "contextual_job_analysis",
    "ChromaSearchTool",
]

