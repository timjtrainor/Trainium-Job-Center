-- Deploy career_trainium:update_schema_to_positioning to pg

BEGIN;

-- deploy/update_schema_to_positioning.sql

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop obsolete views and tables
DROP VIEW IF EXISTS contact_details CASCADE;
DROP TABLE IF EXISTS
    resumes_old,
    resume_tags,
    resume_resume_versions,
    resume_accomplishment_tags;

-- Update companies
ALTER TABLE companies
    ALTER COLUMN industry TYPE jsonb USING to_jsonb(industry),
    DROP COLUMN created_at;

-- Update contacts
ALTER TABLE contacts
    ALTER COLUMN strategic_alignment_score TYPE numeric USING strategic_alignment_score::numeric;

-- Update user_positioning_profiles
ALTER TABLE user_positioning_profiles
    ADD COLUMN positioning_summary TEXT,
    ADD COLUMN core_narrative TEXT,
    ADD COLUMN highlight_1 TEXT,
    ADD COLUMN highlight_2 TEXT,
    ADD COLUMN highlight_3 TEXT,
    ADD COLUMN highlight_4 TEXT,
    ADD COLUMN effectiveness_statement TEXT,
    ADD COLUMN connection_invite_prompt TEXT;

-- Update certifications
ALTER TABLE resume_certifications
    RENAME COLUMN authority TO organization;

-- Update messages
ALTER TABLE messages
    ADD COLUMN is_user_sent BOOLEAN;

-- Update post_engagements
ALTER TABLE post_engagements
    DROP COLUMN contact_id,
    ADD COLUMN contact_name TEXT NOT NULL,
    ADD COLUMN contact_title TEXT,
    ADD COLUMN interaction_type TEXT,
    ADD COLUMN content TEXT,
    ADD COLUMN contact_linkedin_url TEXT,
    ADD COLUMN notes TEXT,
    ADD COLUMN post_theme TEXT;

-- Update linkedin_posts
ALTER TABLE linkedin_posts
    ADD COLUMN tags TEXT[];

-- Update post_responses
ALTER TABLE post_responses
    ADD COLUMN conversation JSONB,
    ALTER COLUMN post_excerpt SET NOT NULL;

-- Update FK from users to profiles
ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_user_profile;

ALTER TABLE users
    ADD CONSTRAINT fk_user_profile
    FOREIGN KEY (user_id)
    REFERENCES user_positioning_profiles(user_id)
    ON DELETE CASCADE DEFERRABLE;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_job_applications_company_id ON job_applications(company_id);
CREATE INDEX IF NOT EXISTS idx_job_applications_status_id ON job_applications(status_id);
CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_contacts_job_application_id ON contacts(job_application_id);
CREATE INDEX IF NOT EXISTS idx_messages_contact_id ON messages(contact_id);
CREATE INDEX IF NOT EXISTS idx_messages_job_application_id ON messages(job_application_id);
CREATE INDEX IF NOT EXISTS idx_interviews_job_application_id ON interviews(job_application_id);
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);

COMMIT;
