-- Revert career_trainium:add_job_status_field from pg

BEGIN;

-- Drop the status field and its associated objects
DROP INDEX IF EXISTS idx_jobs_updated_at;
DROP INDEX IF EXISTS idx_jobs_status;
ALTER TABLE public.jobs DROP CONSTRAINT IF EXISTS jobs_status_check;
ALTER TABLE public.jobs DROP COLUMN IF EXISTS updated_at;
ALTER TABLE public.jobs DROP COLUMN IF EXISTS status;

COMMIT;