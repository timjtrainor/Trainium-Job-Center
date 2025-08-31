-- Check for user_id
SELECT column_name FROM information_schema.columns
WHERE table_name IN ('job_applications', 'linkedin_posts', 'resumes')
  AND column_name = 'user_id';