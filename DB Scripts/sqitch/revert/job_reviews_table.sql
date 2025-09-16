-- Revert career_trainium:job_reviews_table from pg

BEGIN;

-- Drop job_reviews table (CASCADE will handle dependent objects)
DROP TABLE IF EXISTS public.job_reviews CASCADE;

COMMIT;