-- Deploy career_trainium:prompt1b-migrate-positioning-profiles to pg

BEGIN;

-- Migrate each user_positioning_profile row into a strategic_narrative
INSERT INTO strategic_narratives (
    narrative_id,
    user_id,
    narrative_name,
    desired_title,
    positioning_statement,
    signature_capability,
    impact_story_title,
    impact_story_body,
    default_resume_id,
    created_at,
    updated_at
)
SELECT
    gen_random_uuid(),
    user_id,
    'Default Narrative',
    desired_title,
    positioning_statement,
    signature_capability,
    impact_story_title,
    impact_story_body,
    default_resume_id,
    now(),
    now()
FROM user_positioning_profiles;

COMMIT;