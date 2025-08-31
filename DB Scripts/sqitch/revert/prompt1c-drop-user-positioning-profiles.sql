-- Revert career_trainium:prompt1c-drop-user-positioning-profiles from pg

BEGIN;

-- Recreate user_positioning_profiles (match old definition)
CREATE TABLE user_positioning_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    desired_title TEXT NOT NULL,
    positioning_statement TEXT,
    signature_capability TEXT,
    impact_story_title TEXT,
    impact_story_body TEXT,
    default_resume_id UUID REFERENCES resumes(resume_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Restore constraints
ALTER TABLE users ADD CONSTRAINT fk_user_profile
    FOREIGN KEY (user_id) REFERENCES user_positioning_profiles(user_id) ON DELETE CASCADE;

ALTER TABLE common_interview_answers ADD CONSTRAINT common_interview_answers_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES user_positioning_profiles(user_id);

COMMIT;