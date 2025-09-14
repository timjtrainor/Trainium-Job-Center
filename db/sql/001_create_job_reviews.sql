-- 001_create_job_reviews.sql
-- Raw SQL migration to create job_reviews table for AI + human review results

BEGIN;

-- job_reviews table for storing AI and human review results for job postings
-- This table enables the job_posting_review crew to persist outcomes and supports future HILT
CREATE TABLE public.job_reviews (
    -- Primary key
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    
    -- Foreign key to jobs table with cascading delete
    job_id uuid NOT NULL,
    
    -- AI review decision and reasoning
    ai_decision text CHECK (ai_decision IN ('approve', 'reject')),
    ai_reason text, -- Can store text or JSON format
    
    -- Human review decision and comment
    human_decision text CHECK (human_decision IN ('approve', 'reject', 'none')) DEFAULT 'none',
    human_comment text,
    
    -- Final decision after considering both AI and human input
    final_decision text CHECK (final_decision IN ('approve', 'reject')) NOT NULL,
    
    -- Timestamp when review was completed
    reviewed_at timestamptz DEFAULT now() NOT NULL,
    
    -- Error message for failed review processes
    error_message text,
    
    -- Constraints
    CONSTRAINT job_reviews_pkey PRIMARY KEY (id),
    CONSTRAINT job_reviews_job_id_fkey FOREIGN KEY (job_id) 
        REFERENCES public.jobs (id) ON DELETE CASCADE,
    CONSTRAINT job_reviews_job_id_unique UNIQUE (job_id)
);

-- Comments documenting the table structure
COMMENT ON TABLE public.job_reviews IS 'Stores AI and human review results for job postings from the job_posting_review crew';
COMMENT ON COLUMN public.job_reviews.job_id IS 'Foreign key to jobs.id with cascade delete - ensures one review per job';
COMMENT ON COLUMN public.job_reviews.ai_decision IS 'AI review decision: approve or reject';
COMMENT ON COLUMN public.job_reviews.ai_reason IS 'AI reasoning for the decision, can be text or JSON format';
COMMENT ON COLUMN public.job_reviews.human_decision IS 'Human override decision: approve, reject, or none (default)';
COMMENT ON COLUMN public.job_reviews.human_comment IS 'Human reviewer comment or notes';
COMMENT ON COLUMN public.job_reviews.final_decision IS 'Final decision after considering AI and human input';
COMMENT ON COLUMN public.job_reviews.reviewed_at IS 'Timestamp when the review was completed';
COMMENT ON COLUMN public.job_reviews.error_message IS 'Error message if the review process failed';

-- Indexes for expected query patterns
CREATE INDEX idx_job_reviews_job_id ON public.job_reviews (job_id);
CREATE INDEX idx_job_reviews_ai_decision ON public.job_reviews (ai_decision) WHERE ai_decision IS NOT NULL;
CREATE INDEX idx_job_reviews_human_decision ON public.job_reviews (human_decision) WHERE human_decision != 'none';
CREATE INDEX idx_job_reviews_final_decision ON public.job_reviews (final_decision);
CREATE INDEX idx_job_reviews_reviewed_at ON public.job_reviews (reviewed_at DESC);

COMMIT;