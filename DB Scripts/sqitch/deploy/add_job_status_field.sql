-- Deploy career_trainium:add_job_status_field to pg

BEGIN;

-- Add status field to jobs table for review workflow
ALTER TABLE public.jobs ADD COLUMN status text DEFAULT 'pending_review' NOT NULL;

-- Add updated_at field for tracking status changes
ALTER TABLE public.jobs ADD COLUMN updated_at timestamptz DEFAULT now() NOT NULL;

-- Add check constraint to ensure valid status values
ALTER TABLE public.jobs ADD CONSTRAINT jobs_status_check 
    CHECK (status IN ('pending_review', 'in_review', 'reviewed', 'archived'));

-- Add index for efficient querying by status
CREATE INDEX idx_jobs_status ON public.jobs (status) WHERE status IN ('pending_review', 'in_review');

-- Add index for updated_at
CREATE INDEX idx_jobs_updated_at ON public.jobs (updated_at DESC);

-- Add comments
COMMENT ON COLUMN public.jobs.status IS 'Review workflow status: pending_review, in_review, reviewed, archived';
COMMENT ON COLUMN public.jobs.updated_at IS 'Timestamp of last status or data update';

COMMIT;