-- Verify career_trainium:prompt1b-migrate-positioning-profiles was deployed

-- Check that at least one row from user_positioning_profiles exists in strategic_narratives
SELECT 1
FROM strategic_narratives
WHERE narrative_name = 'Default Narrative'
LIMIT 1;