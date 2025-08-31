-- Deploy career_trainium:prompt-1-strategic-narratives to pg

BEGIN;

-- Step 1: Add 'narrative_id' to existing tables (nullable for now)
ALTER TABLE job_applications ADD COLUMN narrative_id UUID;
ALTER TABLE linkedin_posts ADD COLUMN narrative_id UUID;

-- Step 2: Create strategic_narratives
CREATE TABLE strategic_narratives (
    narrative_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    narrative_name TEXT NOT NULL,
    desired_title TEXT NOT NULL,
    positioning_statement TEXT,
    signature_capability TEXT,
    impact_story_title TEXT,
    impact_story_body TEXT,
    default_resume_id UUID REFERENCES resumes(resume_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Step 3: Index for user lookups
CREATE INDEX idx_strategic_narratives_user_id ON strategic_narratives(user_id);

-- Step 4: Add foreign keys (with distinct constraint names)
ALTER TABLE job_applications
ADD CONSTRAINT fk_job_applications_narrative
FOREIGN KEY (narrative_id)
REFERENCES strategic_narratives(narrative_id)
ON DELETE SET NULL;

ALTER TABLE linkedin_posts
ADD CONSTRAINT fk_linkedin_posts_narrative
FOREIGN KEY (narrative_id)
REFERENCES strategic_narratives(narrative_id)
ON DELETE SET NULL;

-- Step 5: Create many-to-many table
CREATE TABLE contact_narratives (
    contact_id UUID NOT NULL REFERENCES contacts(contact_id) ON DELETE CASCADE,
    narrative_id UUID NOT NULL REFERENCES strategic_narratives(narrative_id) ON DELETE CASCADE,
    PRIMARY KEY (contact_id, narrative_id)
);

COMMIT;