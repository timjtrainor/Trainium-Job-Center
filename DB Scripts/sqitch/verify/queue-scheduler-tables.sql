-- Verify career_trainium:queue-scheduler-tables on pg

BEGIN;

-- Verify site_schedules table exists with expected structure
SELECT 1/COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'site_schedules';

-- Verify scrape_runs table exists with expected structure  
SELECT 1/COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'scrape_runs';

-- Verify key columns exist
SELECT id, site_name, enabled, interval_minutes, payload FROM site_schedules LIMIT 0;
SELECT id, run_id, task_id, trigger, status FROM scrape_runs LIMIT 0;

-- Verify constraints
SELECT 1/COUNT(*) FROM information_schema.table_constraints 
WHERE table_name = 'site_schedules' AND constraint_name = 'site_schedules_site_name_unique';

-- Verify default data was inserted
SELECT 1/COUNT(*) FROM site_schedules WHERE site_name IN ('indeed', 'linkedin', 'glassdoor', 'ziprecruiter', 'google');

ROLLBACK;