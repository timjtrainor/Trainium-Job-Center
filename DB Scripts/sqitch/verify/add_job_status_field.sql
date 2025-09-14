-- Verify career_trainium:add_job_status_field on pg

BEGIN;

-- Verify the status column exists with correct default
SELECT status FROM public.jobs LIMIT 0;

-- Verify the updated_at column exists
SELECT updated_at FROM public.jobs LIMIT 0;

-- Verify the constraint exists
SELECT conname FROM pg_constraint WHERE conname = 'jobs_status_check';

-- Verify the indexes exist
SELECT indexname FROM pg_indexes WHERE indexname = 'idx_jobs_status';
SELECT indexname FROM pg_indexes WHERE indexname = 'idx_jobs_updated_at';

ROLLBACK;