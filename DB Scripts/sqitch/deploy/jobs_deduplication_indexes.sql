-- Deploy career_trainium:jobs_deduplication_indexes to pg
-- requires: jobs_table_init

BEGIN;

-- Add indexes for deduplication fields to improve query performance
CREATE INDEX idx_jobs_canonical_key ON public.jobs (canonical_key)
    WHERE canonical_key IS NOT NULL;

CREATE INDEX idx_jobs_fingerprint ON public.jobs (fingerprint)
    WHERE fingerprint IS NOT NULL;

CREATE INDEX idx_jobs_duplicate_group_id ON public.jobs (duplicate_group_id)
    WHERE duplicate_group_id IS NOT NULL;

-- Composite index for finding duplicates by canonical_key + fingerprint
CREATE INDEX idx_jobs_canonical_fingerprint ON public.jobs (canonical_key, fingerprint)
    WHERE canonical_key IS NOT NULL AND fingerprint IS NOT NULL;

-- Comments
COMMENT ON INDEX idx_jobs_canonical_key IS 'Index for cross-site deduplication by normalized company+title';
COMMENT ON INDEX idx_jobs_fingerprint IS 'Index for content-based duplicate detection';
COMMENT ON INDEX idx_jobs_duplicate_group_id IS 'Index for grouping duplicate jobs across sites';

COMMIT;
