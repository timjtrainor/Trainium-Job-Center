import asyncio
import os
import json
from uuid import UUID
from dotenv import load_dotenv
from app.services.infrastructure.database_service import get_database_service

load_dotenv()

async def diag():
    db = get_database_service()
    await db.initialize()
    
    async with db.pool.acquire() as conn:
        # Get user
        user_id = await conn.fetchval("SELECT user_id FROM strategic_narratives ORDER BY created_at DESC LIMIT 1")
        print(f"User ID: {user_id}")
        
        # Check jobs
        all_jobs = await conn.fetchval("SELECT count(*) FROM job_applications WHERE user_id = $1", user_id)
        print(f"Total Jobs: {all_jobs}")
        
        # Check jobs in last 30 days
        recent_jobs = await conn.fetchval("SELECT count(*) FROM job_applications WHERE user_id = $1 AND created_at >= NOW() - interval '30 day'", user_id)
        print(f"Jobs (last 30d): {recent_jobs}")
        
        # Check jobs with messages
        jobs_with_messages = await conn.fetchval("SELECT count(DISTINCT job_application_id) FROM messages WHERE job_application_id IS NOT NULL")
        print(f"Jobs with messages: {jobs_with_messages}")
        
        # Check candidates (same logic as TournamentService)
        query = """
        SELECT count(*)
        FROM job_applications ja
        LEFT JOIN statuses s ON ja.status_id = s.status_id
        WHERE ja.user_id = $1
          AND ja.created_at >= NOW() - (30 * interval '1 day')
          AND (s.status_name IS NULL OR s.status_name NOT IN ('Archived', 'Rejected', 'Offer', 'Withdrawn'))
          AND ja.job_application_id NOT IN (
              SELECT DISTINCT job_application_id FROM messages WHERE job_application_id IS NOT NULL
          )
        """
        candidates_count = await conn.fetchval(query, user_id)
        print(f"Eligible Candidates for Ranking: {candidates_count}")

if __name__ == "__main__":
    asyncio.run(diag())
