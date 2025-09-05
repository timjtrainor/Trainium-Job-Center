from langchain.tools import BaseTool
import psycopg, os
from typing import Optional

class PostgresQueryTool(BaseTool):
    name: str = "postgres_query"
    description: str = "Executes a SQL query on the Postgres database and returns results."

    # Declare as Pydantic field
    conn_str: Optional[str] = None

    def _run(self, query: str) -> str:
        conn_str = self.conn_str or os.getenv("DATABASE_URL")
        if not conn_str:
            return "Error: DATABASE_URL not set and no connection string provided."
        try:
            with psycopg.connect(conn_str) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    if cur.description:
                        rows = cur.fetchall()
                        return "\n".join([str(r) for r in rows])
                    else:
                        conn.commit()
                        return "Query executed successfully."
        except Exception as e:
            return f"Error executing query: {e}"