-- Deploy career_trainium:jobs_table_init to pg

BEGIN;

-- jobs table for storing scraped job data from various job boards
-- Types chosen based on JobSpy data format analysis:
-- - text for strings (JobSpy returns variable-length strings)
-- - numeric for salary amounts (JobSpy returns floats, numeric handles precision better)
-- - timestamptz for dates (supports timezone-aware timestamps)
-- - jsonb for source_raw (efficient JSON storage with indexing support)
-- - boolean for is_remote flag
CREATE TABLE public.jobs (
    -- Primary key
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    
    -- Core identification fields (unique constraint on these)
    site text NOT NULL,                    -- Job board name (indeed, linkedin, etc.)
    job_url text NOT NULL,                 -- Canonical job URL (unique with site)
    
    -- Basic job information
    title text,                            -- Job title
    company text,                          -- Company name
    company_url text,                      -- Company URL (not populated by JobSpy currently)
    
    -- Location fields (location parsing not implemented initially)
    location_country text,                 -- Country (placeholder for future parsing)
    location_state text,                   -- State/Province (placeholder)
    location_city text,                    -- City (placeholder) 
    is_remote boolean,                     -- Remote work flag
    
    -- Job details
    job_type text,                         -- Job type (fulltime, contract, etc.)
    
    -- Compensation fields
    compensation text,                     -- Formatted compensation string (placeholder)
    interval text,                         -- yearly, monthly, hourly
    min_amount numeric(12,2),              -- Minimum salary amount (precision for currency)
    max_amount numeric(12,2),              -- Maximum salary amount
    currency text,                         -- Currency code (placeholder, not in JobSpy)
    salary_source text,                    -- Source of salary info (employer, glassdoor, etc.)
    
    -- Content
    description text,                      -- Job description (markdown format from JobSpy)
    
    -- Timestamps
    date_posted timestamptz,               -- When job was originally posted
    ingested_at timestamptz DEFAULT now() NOT NULL, -- When we scraped/stored this record
    
    -- Raw data and future deduplication fields
    source_raw jsonb,                      -- Complete raw JobSpy record for provenance
    canonical_key text,                    -- Future: normalized dedup key (placeholder)
    fingerprint text,                      -- Future: content-based hash (placeholder) 
    duplicate_group_id text,               -- Future: cross-board duplicate grouping (placeholder)
    
    -- Constraints
    CONSTRAINT jobs_pkey PRIMARY KEY (id),
    CONSTRAINT jobs_site_job_url_key UNIQUE (site, job_url)
);

-- Comments documenting the table structure and type choices
COMMENT ON TABLE public.jobs IS 'Stores scraped job postings from various job boards with idempotent upserts on (site, job_url)';
COMMENT ON COLUMN public.jobs.site IS 'Job board identifier (indeed, linkedin, glassdoor, etc.)';  
COMMENT ON COLUMN public.jobs.job_url IS 'Canonical job URL, forms unique constraint with site';
COMMENT ON COLUMN public.jobs.min_amount IS 'Minimum salary as numeric(12,2) to handle currency precision';
COMMENT ON COLUMN public.jobs.max_amount IS 'Maximum salary as numeric(12,2) to handle currency precision'; 
COMMENT ON COLUMN public.jobs.date_posted IS 'Original job posting date with timezone support';
COMMENT ON COLUMN public.jobs.source_raw IS 'Complete JobSpy record as JSONB for provenance and future field extraction';
COMMENT ON COLUMN public.jobs.canonical_key IS 'Future: normalized key for cross-board deduplication';
COMMENT ON COLUMN public.jobs.fingerprint IS 'Future: content hash for semantic duplicate detection';
COMMENT ON COLUMN public.jobs.duplicate_group_id IS 'Future: groups semantically identical jobs across boards';

-- Indexes for expected query patterns
CREATE INDEX idx_jobs_site ON public.jobs (site);
CREATE INDEX idx_jobs_date_posted ON public.jobs (date_posted DESC) WHERE date_posted IS NOT NULL;
CREATE INDEX idx_jobs_ingested_at ON public.jobs (ingested_at DESC);
CREATE INDEX idx_jobs_is_remote ON public.jobs (is_remote) WHERE is_remote = true;
CREATE INDEX idx_jobs_company ON public.jobs (company) WHERE company IS NOT NULL;

-- GIN index on source_raw for efficient JSON queries
CREATE INDEX idx_jobs_source_raw_gin ON public.jobs USING GIN (source_raw);

COMMIT;