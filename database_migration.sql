-- Career Brand Analysis System Migration
-- Adds support for enhanced 9-agent analysis with concrete scoring and HITL UI improvements

-- Add overall_alignment_score as top-level column for UI optimization
ALTER TABLE job_reviews
ADD COLUMN IF NOT EXISTS overall_alignment_score decimal(5,2) NULL;

-- Add analysis version tracking for schema evolution
ALTER TABLE job_reviews
ADD COLUMN IF NOT EXISTS crew_output_version TEXT DEFAULT '1.0';

-- Create indexes for performance on frequently queried columns
CREATE INDEX IF NOT EXISTS idx_job_reviews_overall_alignment_score
ON job_reviews (overall_alignment_score DESC)
WHERE (overall_alignment_score IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_job_reviews_crew_output_version
ON job_reviews (crew_output_version)
WHERE (crew_output_version IS NOT NULL);

-- Add column comments for documentation
COMMENT ON COLUMN job_reviews.overall_alignment_score
IS 'Weighted overall alignment score (0-10) from career brand analysis. Higher scores indicate better career fit. Displayed prominently in HITL job review UI.';

COMMENT ON COLUMN job_reviews.crew_output_version
IS 'Version of crew output format. Enables schema evolution and migration of older analysis records.';

-- Validation: Check existing structure
DO $$
BEGIN
    -- Verify new columns exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'job_reviews'
        AND column_name = 'overall_alignment_score'
    ) THEN
        RAISE EXCEPTION 'overall_alignment_score column was not created successfully';
    END IF;

    -- Verify indexes exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'job_reviews'
        AND indexname = 'idx_job_reviews_overall_alignment_score'
    ) THEN
        RAISE EXCEPTION 'overall_alignment_score index was not created successfully';
    END IF;
END $$;
