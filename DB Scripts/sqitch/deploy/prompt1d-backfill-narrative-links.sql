-- Deploy career_trainium:prompt1d-backfill-narrative-links to pg

BEGIN;

-- Update job_applications with default narrative
UPDATE job_applications AS ja
SET narrative_id = sn.narrative_id
FROM strategic_narratives sn
WHERE ja.user_id = sn.user_id
  AND sn.narrative_name = 'Default Narrative';

-- Update linkedin_posts with default narrative
UPDATE linkedin_posts AS lp
SET narrative_id = sn.narrative_id
FROM strategic_narratives sn
WHERE lp.user_id = sn.user_id
  AND sn.narrative_name = 'Default Narrative';

COMMIT;