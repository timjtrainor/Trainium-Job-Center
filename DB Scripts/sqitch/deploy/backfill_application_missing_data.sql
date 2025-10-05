-- Deploy backfill_application_missing_data to pg
-- Backfill missing job_link, salary, location, and company data for applications created from jobs

BEGIN;

-- Backfill applications missing job_link from their source jobs
UPDATE job_applications
SET job_link = j.job_url
FROM jobs j
WHERE job_applications.source_job_id = j.id
  AND job_applications.source_job_id IS NOT NULL
  AND (job_applications.job_link IS NULL OR job_applications.job_link = '');

-- Backfill applications missing salary from their source jobs
UPDATE job_applications
SET salary = CONCAT('$', j.min_amount::text, '-', j.max_amount::text)
FROM jobs j
WHERE job_applications.source_job_id = j.id
  AND job_applications.source_job_id IS NOT NULL
  AND (job_applications.salary IS NULL OR job_applications.salary = '')
  AND j.min_amount IS NOT NULL;

-- Backfill applications missing location from their source jobs
UPDATE job_applications
SET location = TRIM(
    COALESCE(NULLIF(j.location_city, ''), '') || ', ' ||
    COALESCE(NULLIF(j.location_state, ''), '') || ', ' ||
    COALESCE(NULLIF(j.location_country, ''), ''),
    ', '
)
FROM jobs j
WHERE job_applications.source_job_id = j.id
  AND job_applications.source_job_id IS NOT NULL
  AND (job_applications.location IS NULL OR job_applications.location = '')
  AND (
    j.location_city IS NOT NULL OR
    j.location_state IS NOT NULL OR
    j.location_country IS NOT NULL
  );

-- Backfill company associations for applications missing company_id
-- First, ensure companies exist for job data by creating missing companies
INSERT INTO companies (company_name, company_url, user_id, is_recruiting_firm)
SELECT DISTINCT
    j.company as company_name,
    j.job_url as company_url,
    ja.user_id,
    FALSE as is_recruiting_firm
FROM job_applications ja
JOIN jobs j ON ja.source_job_id = j.id
WHERE ja.source_job_id IS NOT NULL
  AND ja.company_id IS NULL
  AND j.company IS NOT NULL
  AND j.company != ''
  AND NOT EXISTS (
    SELECT 1 FROM companies c
    WHERE c.company_name = j.company
  )
ON CONFLICT (company_name) DO NOTHING;

-- Now update applications to link to companies
UPDATE job_applications
SET company_id = c.company_id
FROM jobs j
JOIN companies c ON c.company_name = j.company
WHERE job_applications.source_job_id = j.id
  AND job_applications.source_job_id IS NOT NULL
  AND job_applications.company_id IS NULL;

-- Update jobs to also have company associations (for consistency)
UPDATE jobs
SET company_id = c.company_id
FROM companies c
WHERE jobs.company_id IS NULL
  AND c.company_name = jobs.company
  AND EXISTS (
    SELECT 1 FROM job_applications ja
    WHERE ja.source_job_id = jobs.id
  );

-- Log the backfill results
DO $$
DECLARE
    total_applications int;
    fixed_links int;
    fixed_salary int;
    fixed_location int;
    fixed_company int;
BEGIN
    SELECT COUNT(*) INTO total_applications
    FROM job_applications
    WHERE source_job_id IS NOT NULL;

    SELECT COUNT(*) INTO fixed_links
    FROM job_applications
    WHERE source_job_id IS NOT NULL
      AND job_link IS NOT NULL
      AND job_link != '';

    SELECT COUNT(*) INTO fixed_salary
    FROM job_applications
    WHERE source_job_id IS NOT NULL
      AND salary IS NOT NULL
      AND salary != '';

    SELECT COUNT(*) INTO fixed_location
    FROM job_applications
    WHERE source_job_id IS NOT NULL
      AND location IS NOT NULL
      AND location != '';

    SELECT COUNT(*) INTO fixed_company
    FROM job_applications
    WHERE source_job_id IS NOT NULL
      AND company_id IS NOT NULL;

    RAISE NOTICE 'Backfill completed for % applications', total_applications;
    RAISE NOTICE '- Job links: % populated', fixed_links;
    RAISE NOTICE '- Salaries: % populated', fixed_salary;
    RAISE NOTICE '- Locations: % populated', fixed_location;
    RAISE NOTICE '- Companies: % linked', fixed_company;
END $$;

COMMIT;
