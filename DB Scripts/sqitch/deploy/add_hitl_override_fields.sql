-- Deploy career_trainium:add_hitl_override_fields to pg

BEGIN;

-- Add HITL (Human-in-the-Loop) override fields to job_reviews table
ALTER TABLE public.job_reviews ADD COLUMN override_recommend BOOLEAN NULL;
ALTER TABLE public.job_reviews ADD COLUMN override_comment TEXT NULL;
ALTER TABLE public.job_reviews ADD COLUMN override_by TEXT NULL;
ALTER TABLE public.job_reviews ADD COLUMN override_at TIMESTAMPTZ NULL;

-- Add index for querying overridden reviews
CREATE INDEX idx_job_reviews_override_recommend ON public.job_reviews (override_recommend) WHERE override_recommend IS NOT NULL;

-- Add index for override timestamp
CREATE INDEX idx_job_reviews_override_at ON public.job_reviews (override_at DESC) WHERE override_at IS NOT NULL;

-- Add comments to document the new fields
COMMENT ON COLUMN public.job_reviews.override_recommend IS 'Human override of AI recommendation: true=recommend, false=do not recommend, null=no override';
COMMENT ON COLUMN public.job_reviews.override_comment IS 'Human reviewer comment explaining the override decision';
COMMENT ON COLUMN public.job_reviews.override_by IS 'Identifier of the human reviewer who made the override';
COMMENT ON COLUMN public.job_reviews.override_at IS 'Timestamp when the human override was made';

COMMIT;