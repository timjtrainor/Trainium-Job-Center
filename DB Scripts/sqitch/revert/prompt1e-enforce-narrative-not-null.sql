-- Revert career_trainium:prompt1e-enforce-narrative-not-null from pg

BEGIN;

-- Allow narrative_id to be NULL again
ALTER TABLE job_applications
ALTER COLUMN narrative_id DROP NOT NULL;

ALTER TABLE linkedin_posts
ALTER COLUMN narrative_id DROP NOT NULL;

COMMIT;