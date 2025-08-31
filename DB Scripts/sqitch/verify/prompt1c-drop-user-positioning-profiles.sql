-- Verify career_trainium:prompt1c-drop-user-positioning-profiles was deployed

SELECT 1
FROM information_schema.tables
WHERE table_name = 'user_positioning_profiles'
  AND table_schema = 'public'
LIMIT 1;