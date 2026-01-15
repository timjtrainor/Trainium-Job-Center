from app.services.infrastructure.database import get_database_service
import asyncio

async def check_statuses():
    db = get_database_service()
    await db.initialize()
    async with db.pool.acquire() as conn:
        statuses = await conn.fetch("SELECT status_id, status_name FROM statuses")
        for s in statuses:
            print(f"ID: {s['status_id']}, Name: {s['status_name']}")

if __name__ == "__main__":
    asyncio.run(check_statuses())
