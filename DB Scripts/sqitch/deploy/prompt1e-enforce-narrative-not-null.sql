-- Deploy career_trainium:prompt1e-enforce-narrative-not-null to pg

BEGIN;

-- Double-check: Ensure there are no nulls (safety guard)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM job_applications WHERE narrative_id IS NULL) THEN
        RAISE EXCEPTION 'job_applications has NULL narrative_id values';
    END IF;

    IF EXISTS (SELECT 1 FROM linkedin_posts WHERE narrative_id IS NULL) THEN
        RAISE EXCEPTION 'linkedin_posts has NULL narrative_id values';
    END IF;
END $$;

-- Now enforce NOT NULL constraint
ALTER TABLE job_applications
ALTER COLUMN narrative_id SET NOT NULL;

ALTER TABLE linkedin_posts
ALTER COLUMN narrative_id SET NOT NULL;

COMMIT;