-- Revert career_trainium:jobs_table_init from pg

BEGIN;

-- Drop the jobs table and all its indexes/constraints
DROP TABLE IF EXISTS public.jobs CASCADE;

COMMIT;