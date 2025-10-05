-- Deploy add_duplicate_status_field to pg
-- Add duplicate_status field to jobs table for preventive deduplication
-- requires: add_job_workflow_enhancements

BEGIN;

-- Add duplicate_status column to jobs table
ALTER TABLE public.jobs
ADD COLUMN IF NOT EXISTS duplicate_status VARCHAR(20) DEFAULT 'original';

-- Add comment explaining the field
COMMENT ON COLUMN public.jobs.duplicate_status IS 'Status of job deduplication: original=first instance, duplicate_hidden=duplicate blocked from processing';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_jobs_duplicate_status ON public.jobs (duplicate_status);

-- Verify the column was added
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'jobs'
        AND column_name = 'duplicate_status'
        AND table_schema = 'public'
    ) THEN
        RAISE EXCEPTION 'duplicate_status column was not created successfully';
    END IF;
END $$;

COMMIT;
