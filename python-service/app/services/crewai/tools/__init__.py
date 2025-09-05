import os
from .custom_pg import PostgresQueryTool


def get_postgres_tool() -> PostgresQueryTool:
    """Create a new PostgresQueryTool instance."""
    conn_str = os.getenv("DATABASE_URL")
    if not conn_str:
        raise ValueError("DATABASE_URL environment variable is not set!")
    return PostgresQueryTool(conn_str=conn_str)


__all__ = ["PostgresQueryTool", "get_postgres_tool"]

