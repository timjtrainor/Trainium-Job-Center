-- Revert career_trainium:queue-scheduler-tables from pg

BEGIN;

-- Drop tables in reverse order of creation
DROP TABLE IF EXISTS scrape_runs;
DROP TABLE IF EXISTS site_schedules;

COMMIT;