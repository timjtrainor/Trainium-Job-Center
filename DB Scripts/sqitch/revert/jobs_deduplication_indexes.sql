-- Revert career_trainium:jobs_deduplication_indexes from pg

BEGIN;

DROP INDEX IF EXISTS public.idx_jobs_canonical_fingerprint;
DROP INDEX IF EXISTS public.idx_jobs_duplicate_group_id;
DROP INDEX IF EXISTS public.idx_jobs_fingerprint;
DROP INDEX IF EXISTS public.idx_jobs_canonical_key;

COMMIT;
