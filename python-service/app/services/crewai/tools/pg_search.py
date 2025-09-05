"""Custom CrewAI tool for searching strategic narratives in Postgres."""

import asyncio
import os
from typing import Optional

import asyncpg


async def _fetch_narratives(narrative_name: Optional[str]) -> str:
    """Query the strategic_narratives table for optional narrative_name."""

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "DATABASE_URL not configured"

    conn = await asyncpg.connect(db_url)

    query = "SELECT narrative_text FROM strategic_narratives"
    params = []
    if narrative_name:
        query += " WHERE narrative_name = $1"
        params.append(narrative_name)

    rows = await conn.fetch(query, *params)
    await conn.close()

    if not rows:
        return "No matching narratives found"

    return "\n\n".join(row["narrative_text"] for row in rows)


def pg_search(narrative_name: Optional[str]) -> str:
    """Synchronously fetch narratives, hiding async complexity from tool users."""

    return asyncio.run(_fetch_narratives(narrative_name))

