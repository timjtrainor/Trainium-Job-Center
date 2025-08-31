-- Verify career_trainium:prompt1e-enforce-narrative-not-null was deployed

-- Check that columns are NOT NULL now
SELECT 1
FROM information_schema.columns
WHERE table_name = 'job_applications'
  AND column_name = 'narrative_id'
  AND is_nullable = 'NO';

SELECT 1
FROM information_schema.columns
WHERE table_name = 'linkedin_posts'
  AND column_name = 'narrative_id'
  AND is_nullable = 'NO';