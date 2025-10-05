-- Test preventive deduplication
-- Insert an original job
INSERT INTO public.jobs (
    site, job_url, title, company, duplicate_status, ingested_at, description,
    job_type, canonical_key, duplicate_group_id, fingerprint
) VALUES (
    'test',
    'https://example.com/job1',
    'Software Engineer',
    'Google',
    'original',
    NOW(),
    'Senior Python developer with machine learning experience required.',
    'full_time',
    'google_software_engineer',
    NULL,
    'test_fingerprint123'
) RETURNING id;

-- Check if the original exists (should return 1 row)
SELECT id FROM public.jobs WHERE canonical_key = 'google_software_engineer' AND duplicate_status = 'original' LIMIT 1;

-- Now insert a duplicate job (this should be blocked and marked as duplicate_hidden)
-- The business logic here is simulated - in real code this happens in job_persistence._upsert_job()
