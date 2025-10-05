-- Deploy add_job_workflow_enhancements
-- Add workflow status and normalization fields to jobs table
-- Add source_job_id to job_applications table
-- Add normalized_name to companies table

BEGIN;

-- Add workflow status to jobs table
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(50) DEFAULT 'pending_review',
ADD COLUMN IF NOT EXISTS scraped_markdown TEXT,
ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS normalized_title VARCHAR(500),
ADD COLUMN IF NOT EXISTS normalized_company VARCHAR(500);

-- Create index for duplicate detection
CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url);
CREATE INDEX IF NOT EXISTS idx_jobs_normalized_fields
ON jobs(normalized_company, normalized_title);
CREATE INDEX IF NOT EXISTS idx_jobs_workflow_status ON jobs(workflow_status);

-- Add source_job_id to applications table
ALTER TABLE job_applications
ADD COLUMN IF NOT EXISTS source_job_id UUID REFERENCES jobs(id),
ADD COLUMN IF NOT EXISTS workflow_mode VARCHAR(50) DEFAULT 'manual'; -- 'ai_generated', 'fast_track', 'manual'

-- Add normalized_name and source to companies
ALTER TABLE companies
ADD COLUMN IF NOT EXISTS normalized_name VARCHAR(500),
ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual';

CREATE INDEX IF NOT EXISTS idx_companies_normalized ON companies(normalized_name);

COMMIT;
