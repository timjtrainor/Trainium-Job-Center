-- Fix JobSpy scheduler issues by enabling schedules and configuring proper pagination
-- Run this script to enable job schedules with high-volume configuration

-- Update Indeed schedule for high-volume scraping
INSERT INTO site_schedules (
    site_name, enabled, interval_minutes, payload, next_run_at,
    min_pause_seconds, max_pause_seconds, max_retries
) VALUES (
    'indeed', true, 120, 
    '{"search_term": "software engineer", "location": "Remote", "is_remote": true, "results_wanted": 100, "country_indeed": "USA"}',
    NOW() + INTERVAL '5 minutes',
    3, 10, 3
) ON CONFLICT (site_name) DO UPDATE SET
    enabled = EXCLUDED.enabled,
    interval_minutes = EXCLUDED.interval_minutes,
    payload = EXCLUDED.payload,
    next_run_at = EXCLUDED.next_run_at,
    min_pause_seconds = EXCLUDED.min_pause_seconds,
    max_pause_seconds = EXCLUDED.max_pause_seconds,
    updated_at = NOW();

-- Update LinkedIn schedule for high-volume scraping  
INSERT INTO site_schedules (
    site_name, enabled, interval_minutes, payload, next_run_at,
    min_pause_seconds, max_pause_seconds, max_retries
) VALUES (
    'linkedin', true, 180,
    '{"search_term": "software engineer", "location": "Remote", "is_remote": true, "results_wanted": 75, "linkedin_fetch_description": true}',
    NOW() + INTERVAL '35 minutes',
    4, 12, 3
) ON CONFLICT (site_name) DO UPDATE SET
    enabled = EXCLUDED.enabled,
    interval_minutes = EXCLUDED.interval_minutes,
    payload = EXCLUDED.payload,  
    next_run_at = EXCLUDED.next_run_at,
    min_pause_seconds = EXCLUDED.min_pause_seconds,
    max_pause_seconds = EXCLUDED.max_pause_seconds,
    updated_at = NOW();

-- Update Glassdoor schedule for medium-volume scraping
INSERT INTO site_schedules (
    site_name, enabled, interval_minutes, payload, next_run_at,
    min_pause_seconds, max_pause_seconds, max_retries  
) VALUES (
    'glassdoor', true, 150,
    '{"search_term": "software engineer", "location": "Remote", "is_remote": true, "results_wanted": 50, "country_indeed": "USA"}',
    NOW() + INTERVAL '65 minutes',
    3, 10, 3
) ON CONFLICT (site_name) DO UPDATE SET
    enabled = EXCLUDED.enabled,
    interval_minutes = EXCLUDED.interval_minutes,
    payload = EXCLUDED.payload,
    next_run_at = EXCLUDED.next_run_at,
    min_pause_seconds = EXCLUDED.min_pause_seconds,
    max_pause_seconds = EXCLUDED.max_pause_seconds,
    updated_at = NOW();

-- Disable low-priority sites for now (can be enabled later)
UPDATE site_schedules 
SET enabled = false, updated_at = NOW()
WHERE site_name IN ('ziprecruiter', 'google');

-- Show final configuration
SELECT 
    site_name,
    enabled,
    interval_minutes,
    payload::json->>'results_wanted' as results_wanted,
    next_run_at,
    created_at,
    updated_at
FROM site_schedules 
ORDER BY enabled DESC, site_name;