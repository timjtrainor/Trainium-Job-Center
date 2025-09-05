import os
import psycopg

def pg_custom_query_tool(query: str) -> str:
    """
    Run a SQL query against PostgreSQL.
    """
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return "DATABASE_URL not set."

    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                if not rows:
                    return "No results found."
                return "\n".join([str(row) for row in rows[:20]])  # safe limit
    except Exception as e:
        return f"Query failed: {e}"
