import os
import pytest

asyncpg = pytest.importorskip("asyncpg")
postgresql = pytest.importorskip("testing.postgresql")


@pytest.mark.asyncio
async def test_persist_jobs_inserts_row():
    """Verify persist_jobs writes a record to PostgreSQL."""
    # Start temporary PostgreSQL instance
    with postgresql.Postgresql() as pg:
        os.environ["DATABASE_URL"] = pg.url()

        # Import after setting DATABASE_URL so services pick it up
        from app.models.jobspy import ScrapedJob
        from app.services.job_persistence import persist_jobs

        # Create jobs table schema
        conn = await asyncpg.connect(pg.url())
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        await conn.execute(
            """
            CREATE TABLE public.jobs (
                id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
                site text NOT NULL,
                job_url text NOT NULL,
                title text,
                company text,
                company_url text,
                location_country text,
                location_state text,
                location_city text,
                is_remote boolean,
                job_type text,
                compensation text,
                interval text,
                min_amount numeric(12,2),
                max_amount numeric(12,2),
                currency text,
                salary_source text,
                description text,
                date_posted timestamptz,
                ingested_at timestamptz DEFAULT now(),
                source_raw jsonb,
                canonical_key text,
                fingerprint text,
                duplicate_group_id text,
                CONSTRAINT jobs_site_job_url_key UNIQUE (site, job_url)
            );
            """
        )
        await conn.close()

        # Persist a sample job
        job = ScrapedJob(
            title="Python Developer",
            company="Acme Corp",
            job_url="https://example.com/job/1",
            site="indeed",
        )
        await persist_jobs([job], "indeed")

        # Confirm row exists with matching fields
        conn = await asyncpg.connect(pg.url())
        row = await conn.fetchrow(
            "SELECT site, job_url, title, company FROM public.jobs WHERE site=$1 AND job_url=$2",
            "indeed",
            "https://example.com/job/1",
        )
        await conn.close()

        assert row is not None
        assert row["title"] == "Python Developer"
        assert row["company"] == "Acme Corp"
