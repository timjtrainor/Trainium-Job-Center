-- Revert add_duplicate_status_field from pg

BEGIN;

-- Drop the index first
DROP INDEX IF EXISTS idx_jobs_duplicate_status;

-- Drop the column
ALTER TABLE public.jobs DROP COLUMN IF EXISTS duplicate_status;

COMMIT;
