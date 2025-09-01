-- Deploy career_trainium:queue-scheduler-tables to pg

BEGIN;

-- Create site_schedules table for managing scheduled job scraping
CREATE TABLE site_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_name TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    interval_minutes INTEGER NOT NULL DEFAULT 60,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}',
    min_pause_seconds INTEGER NOT NULL DEFAULT 2,
    max_pause_seconds INTEGER NOT NULL DEFAULT 8,
    max_retries INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Constraints
    CONSTRAINT site_schedules_site_name_unique UNIQUE (site_name),
    CONSTRAINT site_schedules_interval_positive CHECK (interval_minutes > 0),
    CONSTRAINT site_schedules_pause_valid CHECK (min_pause_seconds <= max_pause_seconds),
    CONSTRAINT site_schedules_retries_valid CHECK (max_retries >= 0)
);

-- Create scrape_runs table for tracking job scraping execution
CREATE TABLE scrape_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id TEXT NOT NULL UNIQUE, -- For external tracking/logging
    site_schedule_id UUID REFERENCES site_schedules(id) ON DELETE SET NULL,
    task_id TEXT, -- Queue task identifier
    trigger TEXT NOT NULL CHECK (trigger IN ('schedule', 'manual')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'succeeded', 'partial', 'failed')),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    requested_pages INTEGER DEFAULT 0,
    completed_pages INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX idx_site_schedules_enabled_next_run ON site_schedules(enabled, next_run_at) WHERE enabled = true;
CREATE INDEX idx_site_schedules_site_name ON site_schedules(site_name);
CREATE INDEX idx_scrape_runs_run_id ON scrape_runs(run_id);
CREATE INDEX idx_scrape_runs_site_schedule_id ON scrape_runs(site_schedule_id);
CREATE INDEX idx_scrape_runs_status ON scrape_runs(status);
CREATE INDEX idx_scrape_runs_trigger ON scrape_runs(trigger);
CREATE INDEX idx_scrape_runs_created_at ON scrape_runs(created_at);

-- Insert default site schedules for supported job sites
INSERT INTO site_schedules (site_name, enabled, interval_minutes, payload) VALUES 
    ('indeed', false, 240, '{"search_term": "software engineer", "location": "remote", "is_remote": true, "results_wanted": 50}'),
    ('linkedin', false, 360, '{"search_term": "software engineer", "location": "remote", "is_remote": true, "results_wanted": 50, "linkedin_fetch_description": true}'),
    ('glassdoor', false, 300, '{"search_term": "software engineer", "location": "remote", "is_remote": true, "results_wanted": 50}'),
    ('ziprecruiter', false, 180, '{"search_term": "software engineer", "location": "remote", "is_remote": true, "results_wanted": 50}'),
    ('google', false, 480, '{"google_search_term": "software engineer jobs remote", "results_wanted": 50}');

COMMIT;