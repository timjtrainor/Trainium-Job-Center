-- Deploy career_trainium:job_reviews_table to pg

BEGIN;

-- Replace the job_reviews table with the schema expected by
-- python-service/app/services/infrastructure/database.py
-- DROP TABLE IF EXISTS public.job_reviews CASCADE;

-- Create job_reviews table for storing AI review results
CREATE TABLE public.job_reviews (
    -- Primary key
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    
    -- Foreign key to jobs table
    job_id uuid NOT NULL,
    
    -- Review results captured by the worker
    recommend boolean NOT NULL,
    confidence text NOT NULL,
    rationale text NOT NULL,
    
    -- Detailed analysis results (JSON)
    personas jsonb,                        -- Individual persona verdicts
    tradeoffs jsonb,                       -- Trade-off analysis
    actions jsonb,                         -- Recommended actions
    sources jsonb,                         -- Information sources used
    
    -- Full crew output for debugging/analysis
    crew_output jsonb,
    
    -- Processing metadata
    processing_time_seconds double precision,
    crew_version text,
    model_used text,
    
    -- Error handling
    error_message text,
    retry_count integer DEFAULT 0,
    
    -- Timestamps
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    
    -- Constraints
    CONSTRAINT job_reviews_pkey PRIMARY KEY (id),
    CONSTRAINT job_reviews_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(id) ON DELETE CASCADE,
    CONSTRAINT job_reviews_job_id_unique UNIQUE (job_id), -- One review per job
    CONSTRAINT job_reviews_retry_count_check CHECK (retry_count >= 0)
);

-- Comments
COMMENT ON TABLE public.job_reviews IS 'Stores AI-powered job posting review results from CrewAI job_posting_review service';
COMMENT ON COLUMN public.job_reviews.job_id IS 'Foreign key reference to jobs.id';
COMMENT ON COLUMN public.job_reviews.recommend IS 'Final recommendation: true=recommend, false=do not recommend';
COMMENT ON COLUMN public.job_reviews.confidence IS 'Confidence level returned by the CrewAI workflow';
COMMENT ON COLUMN public.job_reviews.rationale IS 'Human-readable explanation of the recommendation';
COMMENT ON COLUMN public.job_reviews.personas IS 'JSON array of individual persona evaluations';
COMMENT ON COLUMN public.job_reviews.crew_output IS 'Complete raw output from CrewAI for debugging';
COMMENT ON COLUMN public.job_reviews.error_message IS 'Error details if review failed';
COMMENT ON COLUMN public.job_reviews.retry_count IS 'Number of retry attempts for failed reviews';

-- Indexes for efficient querying
CREATE INDEX idx_job_reviews_job_id ON public.job_reviews (job_id);
CREATE INDEX idx_job_reviews_recommend ON public.job_reviews (recommend);
CREATE INDEX idx_job_reviews_confidence ON public.job_reviews (confidence);
CREATE INDEX idx_job_reviews_created_at ON public.job_reviews (created_at DESC);
CREATE INDEX idx_job_reviews_error_status ON public.job_reviews (error_message) WHERE error_message IS NOT NULL;

-- GIN indexes for efficient JSON queries
CREATE INDEX idx_job_reviews_personas_gin ON public.job_reviews USING GIN (personas);
CREATE INDEX idx_job_reviews_crew_output_gin ON public.job_reviews USING GIN (crew_output);

COMMIT;