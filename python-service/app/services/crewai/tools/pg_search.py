import os
from crewai_tools import PGSearchTool


def pg_search_tool():
    return PGSearchTool(
        db_url=os.getenv("DATABASE_URL"),
        table_name="strategic_narratives",
        content_column="narrative_text",
        metadata_columns=["narrative_name"],
    )
