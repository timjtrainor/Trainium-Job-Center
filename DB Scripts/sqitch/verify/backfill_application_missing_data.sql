-- Verify backfill_application_missing_data on pg

-- Verify that applications created from jobs have required fields populated
DO $$
DECLARE
    total_job_apps int;
    populated_links int;
    populated_salary int;
    populated_location int;
    linked_companies int;
BEGIN
    -- Count applications created from jobs
    SELECT COUNT(*) INTO total_job_apps
    FROM job_applications
    WHERE source_job_id IS NOT NULL;

    -- Check populated fields
    SELECT COUNT(*) INTO populated_links
    FROM job_applications
    WHERE source_job_id IS NOT NULL
      AND job_link IS NOT NULL
      AND job_link != '';

    SELECT COUNT(*) INTO populated_salary
    FROM job_applications
    WHERE source_job_id IS NOT NULL
      AND salary IS NOT NULL
      AND salary != '';

    SELECT COUNT(*) INTO populated_location
    FROM job_applications
    WHERE source_job_id IS NOT NULL
      AND location IS NOT NULL
      AND location != '';

    SELECT COUNT(*) INTO linked_companies
    FROM job_applications
    WHERE source_job_id IS NOT NULL
      AND company_id IS NOT NULL;

    -- Verify backfill was successful
    IF total_job_apps > 0 THEN
        IF populated_links < total_job_apps THEN
            RAISE EXCEPTION 'Not all applications have job_link populated: %/%', populated_links, total_job_apps;
        END IF;

        -- Note: Salary and location may not always be available in job data, so we don't enforce 100%
        -- but at least some should be populated if job data had it
        RAISE NOTICE 'Backfill verification passed:';
        RAISE NOTICE '- Job links: %/% applications populated', populated_links, total_job_apps;
        RAISE NOTICE '- Salaries: %/% applications populated', populated_salary, total_job_apps;
        RAISE NOTICE '- Locations: %/% applications populated', populated_location, total_job_apps;
        RAISE NOTICE '- Companies: %/% applications linked', linked_companies, total_job_apps;
    ELSE
        RAISE NOTICE 'No applications created from jobs found - nothing to verify';
    END IF;
END $$;
