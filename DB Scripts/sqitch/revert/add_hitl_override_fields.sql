-- Revert career_trainium:add_hitl_override_fields from pg

BEGIN;

-- Drop the HITL override fields and their associated objects
DROP INDEX IF EXISTS idx_job_reviews_override_at;
DROP INDEX IF EXISTS idx_job_reviews_override_recommend;
ALTER TABLE public.job_reviews DROP COLUMN IF EXISTS override_at;
ALTER TABLE public.job_reviews DROP COLUMN IF EXISTS override_by;
ALTER TABLE public.job_reviews DROP COLUMN IF EXISTS override_comment;
ALTER TABLE public.job_reviews DROP COLUMN IF EXISTS override_recommend;

COMMIT;