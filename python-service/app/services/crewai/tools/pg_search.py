from crewai_tools import PGSearchTool
import os

PG_URL = os.getenv("DATABASE_URL")

def pg_search_tool():
    return PGSearchTool(
        db_url=os.getenv("PG_URL"),
        table_name="strategic_narratives",
        content_column="narrative_text",
        metadata_columns=["narrative_name"]
    )