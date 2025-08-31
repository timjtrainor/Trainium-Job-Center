-- Revert career_trainium:prompt1d-backfill-narrative-links from pg

BEGIN;

-- Set narrative_id back to NULL
UPDATE job_applications SET narrative_id = NULL;
UPDATE linkedin_posts SET narrative_id = NULL;

COMMIT;