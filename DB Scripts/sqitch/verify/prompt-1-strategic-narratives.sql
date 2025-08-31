-- Verify career_trainium:prompt-1-strategic-narratives was deployed

-- Verify strategic_narratives exists
SELECT 1 FROM information_schema.tables
WHERE table_name = 'strategic_narratives';

-- Verify columns added to job_applications and linkedin_posts
SELECT 1 FROM information_schema.columns
WHERE table_name = 'job_applications' AND column_name = 'narrative_id';

SELECT 1 FROM information_schema.columns
WHERE table_name = 'linkedin_posts' AND column_name = 'narrative_id';

-- Verify contact_narratives junction
SELECT 1 FROM information_schema.tables
WHERE table_name = 'contact_narratives';