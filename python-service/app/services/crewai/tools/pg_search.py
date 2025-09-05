import os
from typing import Optional, Dict
from crewai_tools import PGSearchTool


def pg_search_tool(narrative_name: Optional[str] = None) -> PGSearchTool:
    """Create a PGSearchTool configured for strategic narratives.

    Args:
        narrative_name: Optional narrative name to filter search results.

    Returns:
        Configured PGSearchTool instance.
    """
    filters: Optional[Dict[str, str]] = None
    if narrative_name:
        filters = {"narrative_name": narrative_name}
    return PGSearchTool(
        db_url=os.getenv("DATABASE_URL"),
        table_name="strategic_narratives",
        content_column="narrative_text",
        metadata_columns=["narrative_name"],
        filters=filters,
    )
