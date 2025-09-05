# Queue-Based Job Scraping System

This document describes the queue-based job scraping system implemented for the Trainium Job Center.

## Architecture Overview

The system implements a queue + worker model using **RQ (Redis Queue)** for scheduled and ad-hoc job scraping while retaining existing API endpoints.

### Components

1. **Shared Scraping Function** (`app/services/jobspy/scraping.py`)
   - Single source of truth for job scraping logic
   - Used by both workers and sync endpoints
   - Implements randomized human-like pauses

2. **Queue System** (`app/services/infrastructure/queue.py`)
   - RQ-based job queuing with Redis backend
   - Task management and status tracking
   - Redis-based locking for preventing duplicate runs

3. **Worker Processes** (`app/services/infrastructure/worker.py`)
   - Consume jobs from Redis queue
   - Execute scraping with error handling and retries
   - Update run status in database

4. **Scheduler** (`scheduler_daemon.py`)
   - Reads `site_schedules` table for enabled sites
   - Enqueues jobs based on intervals with jitter
   - Prevents overlapping runs per site

5. **Database Tables**
   - `site_schedules`: Site configuration and timing
   - `scrape_runs`: Execution tracking and audit trail

## Database Schema

### site_schedules
```sql
CREATE TABLE site_schedules (
    id UUID PRIMARY KEY,
    site_name TEXT NOT NULL UNIQUE,
    enabled BOOLEAN NOT NULL DEFAULT true,
    interval_minutes INTEGER NOT NULL DEFAULT 60,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    payload JSONB NOT NULL DEFAULT '{}',
    min_pause_seconds INTEGER NOT NULL DEFAULT 2,
    max_pause_seconds INTEGER NOT NULL DEFAULT 8,
    max_retries INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### scrape_runs
```sql
CREATE TABLE scrape_runs (
    id UUID PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE,
    site_schedule_id UUID REFERENCES site_schedules(id),
    task_id TEXT,
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
```

## API Endpoints

### Existing Endpoints (Unchanged)
- `GET /jobs/sites` - Get supported job sites information

### Enhanced Endpoints
- `POST /jobs/scrape` - Scrape jobs (async by default, optional sync mode)
- `GET /jobs/scrape/{run_id}` - Get scraping job status and results

### New Endpoints
- `GET /jobs/queue/status` - Queue metrics and information
- `POST /scheduler/run` - Manually trigger scheduler
- `GET /scheduler/status` - Scheduler status and statistics

## Usage Examples

### Async Scraping (Default)
```bash
curl -X POST "http://localhost:8000/jobs/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "indeed",
    "search_term": "python developer",
    "location": "remote",
    "is_remote": true,
    "results_wanted": 50
  }'
```

Response:
```json
{
  "status": "success",
  "data": {
    "task_id": "run_a1b2c3d4",
    "run_id": "manual_a1b2c3d4", 
    "status": "queued",
    "execution_mode": "async"
  }
}
```

### Sync Scraping (Small/Diagnostic Runs)
```bash
curl -X POST "http://localhost:8000/jobs/scrape?mode=sync" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "indeed",
    "search_term": "python developer",
    "results_wanted": 15
  }'
```

### Check Job Status
```bash
curl "http://localhost:8000/jobs/scrape/manual_a1b2c3d4"
```

## Deployment

### Requirements
- Redis server for queue backend
- PostgreSQL database with schema migrations applied
- Python dependencies from `requirements.txt`

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/trainium

# Redis  
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Queue Configuration
RQ_QUEUE_NAME=scraping
RQ_RESULT_TTL=3600
RQ_JOB_TIMEOUT=900
```

### Running Components

1. **Apply Database Migrations**
   ```bash
   cd "DB Scripts/sqitch"
   export PG_LOCAL_URI="db:pg://user:pass@localhost:5432/trainium"
   sqitch deploy
   ```

2. **Start FastAPI Application**
   ```bash
   cd python-service
   python main.py
   ```

3. **Start Worker Processes**
   ```bash
   cd python-service
   python worker.py
   ```

4. **Start Scheduler Daemon**
   ```bash
   cd python-service  
   python scheduler_daemon.py
   ```

### Docker Deployment
The system is designed to run in containers with:
- FastAPI app container
- Worker container(s) - can scale horizontally
- Scheduler container (single instance)
- Redis container
- PostgreSQL container

## Monitoring and Observability

### Structured Logging
All components emit JSON logs with correlation IDs:
```json
{
  "ts": "2025-01-24T12:00:00Z",
  "site_name": "indeed", 
  "run_id": "sched_abc123",
  "task_id": "rq_task_456",
  "event": "started",
  "status": "running"
}
```

### Key Metrics
- Queue depth and processing latency
- Success/failure rates by site
- Run duration and job counts
- Error rates and retry patterns

### Health Checks
- `GET /health` - Overall system health
- `GET /jobs/health` - JobSpy service + queue system
- `GET /scheduler/status` - Scheduler status

## Security

- Workers and scheduler run inside the cluster (no public exposure)
- Redis-based locking prevents duplicate site runs
- Sync mode has limits (≤25 results) and short timeouts
- Database connections use connection pooling with limits

## Error Handling

### Worker Error Handling
- Automatic retries with exponential backoff
- Status tracking: `succeeded`, `partial` (≤30% errors), `failed`
- Detailed error logging with correlation IDs

### Scheduler Error Handling  
- Per-site locking prevents overlapping runs
- Graceful handling of Redis/database failures
- Jitter (±10%) prevents thundering herd

## Future Enhancements

1. **Job Persistence** - Store scraped jobs in database with deduplication
2. **Advanced Scheduling** - Cron-like expressions, site-specific schedules  
3. **Horizontal Scaling** - Multiple scheduler instances with leader election
4. **Monitoring Dashboard** - Real-time queue and worker metrics
5. **Rate Limiting** - Per-site rate limits and backoff strategies