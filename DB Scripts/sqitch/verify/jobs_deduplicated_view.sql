-- Verify career_trainium:jobs_deduplicated_view on pg

BEGIN;

-- Verify view exists
SELECT 1/COUNT(*) FROM pg_views
WHERE schemaname = 'public'
AND viewname = 'jobs_deduplicated';

-- Verify view has expected columns
SELECT
    id,
    site,
    job_url,
    title,
    company,
    canonical_key,
    fingerprint,
    found_on_sites,
    duplicate_count,
    all_urls
FROM public.jobs_deduplicated
WHERE FALSE;

ROLLBACK;
