-- Revert career_trainium:prompt-1-strategic-narratives from pg

BEGIN;

-- Step 1: Drop contact_narratives junction
DROP TABLE IF EXISTS contact_narratives;

-- Step 2: Drop foreign key constraints
ALTER TABLE linkedin_posts
DROP CONSTRAINT IF EXISTS fk_linkedin_posts_narrative;

ALTER TABLE job_applications
DROP CONSTRAINT IF EXISTS fk_job_applications_narrative;

-- Step 3: Drop columns
ALTER TABLE linkedin_posts
DROP COLUMN IF EXISTS narrative_id;

ALTER TABLE job_applications
DROP COLUMN IF EXISTS narrative_id;

-- Step 4: Drop index
DROP INDEX IF EXISTS idx_strategic_narratives_user_id;

-- Step 5: Drop strategic_narratives table
DROP TABLE IF EXISTS strategic_narratives;

COMMIT;