-- Verify career_trainium:job_reviews_table on pg

BEGIN;

-- Check that job_reviews table exists with expected structure
SELECT id, job_id, recommend, confidence, rationale, personas, tradeoffs, actions, sources, 
       crew_output, processing_time_seconds, crew_version, model_used, error_message, 
       retry_count, created_at, updated_at
FROM public.job_reviews
WHERE FALSE;

-- Check constraints exist
SELECT 1/COUNT(*) FROM pg_constraint WHERE conname = 'job_reviews_job_id_fkey';
SELECT 1/COUNT(*) FROM pg_constraint WHERE conname = 'job_reviews_job_id_unique';
SELECT 1/COUNT(*) FROM pg_constraint WHERE conname = 'job_reviews_retry_count_check';

-- Check indexes exist
SELECT 1/COUNT(*) FROM pg_indexes WHERE indexname = 'idx_job_reviews_job_id';
SELECT 1/COUNT(*) FROM pg_indexes WHERE indexname = 'idx_job_reviews_recommend';
SELECT 1/COUNT(*) FROM pg_indexes WHERE indexname = 'idx_job_reviews_confidence';

ROLLBACK;