import os
from .custom_pg import PostgresQueryTool
from .chroma_search import (
    ChromaSearchTool,
    chroma_search,
    chroma_list_collections,
    chroma_search_across_collections,
)
from crewai.tools import tool


def get_postgres_tool() -> PostgresQueryTool:
    """Create a new PostgresQueryTool instance."""
    conn_str = os.getenv("DATABASE_URL")
    if not conn_str:
        raise ValueError("DATABASE_URL environment variable is not set!")
    return PostgresQueryTool(conn_str=conn_str)


def get_chroma_search_tool(collection_name: str, n_results: int = 4) -> ChromaSearchTool:
    """Create a ChromaSearchTool for the given collection (legacy support)."""
    return ChromaSearchTool(collection_name=collection_name, n_results=n_results)


def get_chroma_tools() -> list:
    """Get all ChromaDB tools for use in CrewAI agents."""
    return [
        chroma_search,
        chroma_list_collections,
        chroma_search_across_collections,
    ]


__all__ = [
    "tool",
    "PostgresQueryTool",
    "get_postgres_tool",
    "ChromaSearchTool",
    "get_chroma_search_tool",
    "chroma_search",
    "chroma_list_collections", 
    "chroma_search_across_collections",
    "get_chroma_tools",
]

