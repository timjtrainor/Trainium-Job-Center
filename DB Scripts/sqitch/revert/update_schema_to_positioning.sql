-- Revert career_trainium:update_schema_to_positioning from pg

BEGIN;

-- revert/update_schema_to_positioning.sql

-- Reverse column additions
ALTER TABLE user_positioning_profiles
    DROP COLUMN IF EXISTS positioning_summary,
    DROP COLUMN IF EXISTS core_narrative,
    DROP COLUMN IF EXISTS highlight_1,
    DROP COLUMN IF EXISTS highlight_2,
    DROP COLUMN IF EXISTS highlight_3,
    DROP COLUMN IF EXISTS highlight_4,
    DROP COLUMN IF EXISTS effectiveness_statement,
    DROP COLUMN IF EXISTS connection_invite_prompt;

-- Revert column rename
ALTER TABLE resume_certifications
    RENAME COLUMN organization TO authority;

-- Revert column changes on contacts
ALTER TABLE contacts
    ALTER COLUMN strategic_alignment_score TYPE int4 USING strategic_alignment_score::int;

-- Revert added columns
ALTER TABLE messages DROP COLUMN IF EXISTS is_user_sent;
ALTER TABLE linkedin_posts DROP COLUMN IF EXISTS tags;
ALTER TABLE post_responses DROP COLUMN IF EXISTS conversation;

-- Revert changes to post_engagements
ALTER TABLE post_engagements
    DROP COLUMN IF EXISTS contact_name,
    DROP COLUMN IF EXISTS contact_title,
    DROP COLUMN IF EXISTS interaction_type,
    DROP COLUMN IF EXISTS content,
    DROP COLUMN IF EXISTS contact_linkedin_url,
    DROP COLUMN IF EXISTS notes,
    DROP COLUMN IF EXISTS post_theme;

-- Recreate contact_id on post_engagements
ALTER TABLE post_engagements ADD COLUMN contact_id UUID;

-- Recreate dropped objects (optional, only if needed)
-- CREATE TABLE resumes_old ...
-- CREATE VIEW contact_details ...


COMMIT;
