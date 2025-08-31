-- Deploy career_trainium:prompt1c-drop-user-positioning-profiles to pg

BEGIN;

-- Drop dependent constraints
ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_user_profile;
ALTER TABLE common_interview_answers DROP CONSTRAINT IF EXISTS common_interview_answers_user_id_fkey;

-- Now it's safe to drop the table
DROP TABLE IF EXISTS user_positioning_profiles;

COMMIT;