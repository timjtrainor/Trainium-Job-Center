-- Verify career_trainium:jobs_deduplication_indexes on pg

BEGIN;

-- Verify indexes exist
SELECT 1/COUNT(*) FROM pg_indexes
WHERE schemaname = 'public'
AND tablename = 'jobs'
AND indexname = 'idx_jobs_canonical_key';

SELECT 1/COUNT(*) FROM pg_indexes
WHERE schemaname = 'public'
AND tablename = 'jobs'
AND indexname = 'idx_jobs_fingerprint';

SELECT 1/COUNT(*) FROM pg_indexes
WHERE schemaname = 'public'
AND tablename = 'jobs'
AND indexname = 'idx_jobs_duplicate_group_id';

SELECT 1/COUNT(*) FROM pg_indexes
WHERE schemaname = 'public'
AND tablename = 'jobs'
AND indexname = 'idx_jobs_canonical_fingerprint';

ROLLBACK;
