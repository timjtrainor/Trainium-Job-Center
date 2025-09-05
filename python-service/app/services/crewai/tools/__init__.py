import os
from .custom_pg import PostgresQueryTool

# Load connection URL from environment
conn_str = os.getenv("DATABASE_URL")

if not conn_str:
    raise ValueError("DATABASE_URL environment variable is not set!")

# Instantiate the Postgres tool once at import time (use keyword argument!)
postgres_tool = PostgresQueryTool(conn_str=conn_str)
