-- Verify career_trainium:jobs_table_init on pg

BEGIN;

-- Verify the jobs table exists
SELECT 1/COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'jobs';

-- Verify the unique constraint on (site, job_url) exists  
SELECT 1/COUNT(*) FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'public' 
  AND tc.table_name = 'jobs'
  AND tc.constraint_type = 'UNIQUE'
  AND tc.constraint_name = 'jobs_site_job_url_key';

-- Verify expected columns exist (by name - types are checked implicitly by deploy script)
DO $verify$
DECLARE
    expected_columns text[] := ARRAY[
        'id', 'site', 'job_url', 'title', 'company', 'company_url',
        'location_country', 'location_state', 'location_city', 'is_remote', 
        'job_type', 'compensation', 'interval', 'min_amount', 'max_amount', 
        'currency', 'salary_source', 'description', 'date_posted', 
        'ingested_at', 'source_raw', 'canonical_key', 'fingerprint', 
        'duplicate_group_id'
    ];
    col text;
    missing_count int := 0;
BEGIN
    FOREACH col IN ARRAY expected_columns LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = 'jobs' 
              AND column_name = col
        ) THEN
            RAISE NOTICE 'Missing column: %', col;
            missing_count := missing_count + 1;
        END IF;
    END LOOP;
    
    IF missing_count > 0 THEN
        RAISE EXCEPTION 'jobs table missing % expected columns', missing_count;
    END IF;
END;
$verify$;

-- Verify primary key exists on id column
SELECT 1/COUNT(*) FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'public' 
  AND tc.table_name = 'jobs'
  AND tc.constraint_type = 'PRIMARY KEY'
  AND tc.constraint_name = 'jobs_pkey';

ROLLBACK;