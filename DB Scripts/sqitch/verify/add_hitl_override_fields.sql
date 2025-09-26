-- Verify career_trainium:add_hitl_override_fields on pg

BEGIN;

-- Verify the new columns exist
SELECT override_recommend FROM public.job_reviews LIMIT 0;
SELECT override_comment FROM public.job_reviews LIMIT 0;
SELECT override_by FROM public.job_reviews LIMIT 0;
SELECT override_at FROM public.job_reviews LIMIT 0;

-- Verify the indexes exist
SELECT indexname FROM pg_indexes WHERE indexname = 'idx_job_reviews_override_recommend';
SELECT indexname FROM pg_indexes WHERE indexname = 'idx_job_reviews_override_at';

-- Verify the columns are nullable (should not error on null inserts)
INSERT INTO public.job_reviews (job_id, recommend, confidence, rationale) 
VALUES (gen_random_uuid(), true, 'high', 'test rationale')
ON CONFLICT (job_id) DO NOTHING;

ROLLBACK;