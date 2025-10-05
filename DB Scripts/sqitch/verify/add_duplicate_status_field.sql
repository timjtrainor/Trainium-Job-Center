-- Verify add_duplicate_status_field on pg

-- Verify the column exists
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'jobs'
AND column_name = 'duplicate_status'
AND table_schema = 'public';

-- Verify it has the correct default
SELECT ad.adsrc AS default_value
FROM pg_attrdef ad
JOIN pg_attribute a ON ad.adrelid = a.attrelid AND ad.adnum = a.attnum
JOIN pg_class c ON a.attrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
WHERE n.nspname = 'public'
AND c.relname = 'jobs'
AND a.attname = 'duplicate_status';

-- Verify the index exists
SELECT indexname, tablename, indexdef
FROM pg_indexes
WHERE tablename = 'jobs'
AND indexname = 'idx_jobs_duplicate_status';
