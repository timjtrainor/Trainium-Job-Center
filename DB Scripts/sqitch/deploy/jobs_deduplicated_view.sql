-- Deploy career_trainium:jobs_deduplicated_view to pg
-- requires: jobs_table_init
-- requires: jobs_deduplication_indexes

BEGIN;

-- Create a view that shows only the best version of each duplicate group
-- For use in job review UI to avoid showing the same job multiple times
CREATE OR REPLACE VIEW public.jobs_deduplicated AS
SELECT DISTINCT ON (COALESCE(canonical_key, id::text))
    j.id,
    j.site,
    j.job_url,
    j.title,
    j.company,
    j.location_country,
    j.location_state,
    j.location_city,
    j.is_remote,
    j.job_type,
    j.compensation,
    j.interval,
    j.min_amount,
    j.max_amount,
    j.currency,
    j.salary_source,
    j.description,
    j.date_posted,
    j.ingested_at,
    j.canonical_key,
    j.fingerprint,
    j.duplicate_group_id,
    j.duplicate_status,
    -- Aggregated fields showing all sites where this job was found
    ARRAY_AGG(j.site) OVER (
        PARTITION BY COALESCE(canonical_key, id::text)
    ) as found_on_sites,
    -- Count of duplicates
    COUNT(*) OVER (
        PARTITION BY COALESCE(canonical_key, id::text)
    ) as duplicate_count,
    -- Array of all job URLs for this duplicate group
    ARRAY_AGG(j.job_url) OVER (
        PARTITION BY COALESCE(canonical_key, id::text)
    ) as all_urls
FROM public.jobs j
ORDER BY
    COALESCE(canonical_key, id::text),
    -- Prioritization logic: prefer jobs with more complete information
    -- 1. Prefer jobs with duplicate_status = 'original' (not hidden duplicates)
    CASE WHEN j.duplicate_status = 'original' THEN 0 ELSE 1 END,
    -- 2. Prefer jobs with salary information
    CASE WHEN j.min_amount IS NOT NULL THEN 0 ELSE 1 END,
    -- 3. Prefer most recently posted
    j.date_posted DESC NULLS LAST,
    -- 4. Prefer earliest ingestion (first discovered)
    j.ingested_at ASC;

-- Comments
COMMENT ON VIEW public.jobs_deduplicated IS 'Deduplicated view of jobs showing only the best version of each duplicate group. Used by job review UI to prevent showing the same job multiple times.';

COMMIT;
