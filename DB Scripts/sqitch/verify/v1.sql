BEGIN;
SELECT 1 FROM public.users LIMIT 1;
SELECT 1 FROM public.job_applications LIMIT 1;
COMMIT;
