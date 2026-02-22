CREATE TABLE IF NOT EXISTS networking_leaderboard (
    rank INT PRIMARY KEY CHECK (rank >= 1 AND rank <= 10),
    job_application_id UUID REFERENCES job_applications(job_application_id) ON DELETE CASCADE,
    pov_hook TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
