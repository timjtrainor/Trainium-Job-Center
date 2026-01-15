import asyncio
import sys
import os

# Add python-service to path
sys.path.insert(0, os.path.join(os.getcwd(), 'python-service'))

from app.services.infrastructure.database import get_database_service
from app.core.config import get_settings

async def create_table():
    settings = get_settings()
    # Construct local URL if not set (config.py expects it to be set)
    if not settings.database_url:
        user = os.getenv("POSTGRES_USER", "trainium_user")
        password = os.getenv("POSTGRES_PASSWORD", "changeme")
        db_name = os.getenv("POSTGRES_DB", "trainium")
        port = os.getenv("POSTGRES_PORT", "5434")
        settings.database_url = f"postgres://{user}:{password}@localhost:{port}/{db_name}"
    
    db = get_database_service()
    await db.initialize()
    
    query = """
    CREATE TABLE IF NOT EXISTS public.webhook_configurations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        redis_channel TEXT NOT NULL,
        webhook_url TEXT NOT NULL,
        auth_token TEXT,
        active BOOLEAN DEFAULT true,
        description TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Grant permissions if necessary (PostgREST usually needs this)
    GRANT ALL ON public.webhook_configurations TO trainium_user;
    """
    
    try:
        async with db.pool.acquire() as conn:
            await conn.execute(query)
            print("Successfully created public.webhook_configurations table.")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(create_table())
