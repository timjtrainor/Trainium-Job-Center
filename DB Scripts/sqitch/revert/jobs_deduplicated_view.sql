-- Revert career_trainium:jobs_deduplicated_view from pg

BEGIN;

DROP VIEW IF EXISTS public.jobs_deduplicated;

COMMIT;
