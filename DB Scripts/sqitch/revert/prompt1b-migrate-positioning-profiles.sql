-- Revert career_trainium:prompt1b-migrate-positioning-profiles from pg

BEGIN;

-- Delete migrated narratives that were inserted during this migration
-- Only deletes those matching the name used in the migration
DELETE FROM strategic_narratives
WHERE narrative_name = 'Default Narrative';

COMMIT;