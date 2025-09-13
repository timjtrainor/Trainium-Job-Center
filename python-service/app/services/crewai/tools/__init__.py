import os
from .custom_pg import PostgresQueryTool
from .chroma_search import ChromaSearchTool
from crewai_tools import tool


def get_postgres_tool() -> PostgresQueryTool:
    """Create a new PostgresQueryTool instance."""
    conn_str = os.getenv("DATABASE_URL")
    if not conn_str:
        raise ValueError("DATABASE_URL environment variable is not set!")
    return PostgresQueryTool(conn_str=conn_str)


def get_chroma_search_tool(collection_name: str, n_results: int = 4) -> ChromaSearchTool:
    """Create a ChromaSearchTool for the given collection."""
    return ChromaSearchTool(collection_name=collection_name, n_results=n_results)


__all__ = [
    "tool",
    "PostgresQueryTool",
    "get_postgres_tool",
    "ChromaSearchTool",
    "get_chroma_search_tool",
]

