# Poller Service Documentation

## Overview

The Poller Service is a lightweight background service that monitors the jobs table for new job postings pending review and automatically enqueues them into Redis for asynchronous processing by the job review pipeline.

## Features

- **Automatic Job Detection**: Polls the jobs table every 5 minutes (configurable) for jobs with `status='pending_review'`
- **Redis Queue Integration**: Enqueues jobs to a dedicated `job_review` Redis queue for processing
- **Status Management**: Updates job status from `pending_review` to `in_review` after successful enqueueing
- **Comprehensive Logging**: Logs all enqueue events with job details (job_id, title, company, site, task_id)
- **Configurable Polling**: Poll interval can be configured via environment variables
- **Independent Service**: Runs as a standalone container service

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Jobs Table    │    │  Poller Service │    │  Redis Queue    │
│                 │    │                 │    │                 │
│ status:         │◄───┤ 1. Poll for     │───►│ job_review      │
│ pending_review  │    │    pending jobs │    │ queue           │
│ ↓               │    │ 2. Enqueue job  │    │                 │
│ in_review       │    │ 3. Update status│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                               ┌─────────────────┐
                                               │ Worker Process  │
                                               │                 │
                                               │ Processes job   │
                                               │ review tasks    │
                                               └─────────────────┘
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Poller configuration
POLL_INTERVAL_MINUTES=5              # How often to check for new jobs (default: 5 minutes)
JOB_REVIEW_QUEUE_NAME=job_review     # Redis queue name for job reviews (default: job_review)

# Database and Redis (should already be configured)
DATABASE_URL=postgres://user:password@db:5432/trainium
REDIS_URL=redis://redis:6379/0
```

## Database Schema

The poller requires the `add_job_status_field` migration to be applied:

```sql
-- Adds status and updated_at fields to jobs table
ALTER TABLE public.jobs ADD COLUMN status text DEFAULT 'pending_review' NOT NULL;
ALTER TABLE public.jobs ADD COLUMN updated_at timestamptz DEFAULT now() NOT NULL;

-- Valid status values: 'pending_review', 'in_review', 'reviewed', 'archived'
ALTER TABLE public.jobs ADD CONSTRAINT jobs_status_check 
    CHECK (status IN ('pending_review', 'in_review', 'reviewed', 'archived'));
```

## Deployment

### 1. Apply Database Migration

```bash
# Navigate to DB Scripts directory
cd "DB Scripts/sqitch"

# Deploy the migration
sqitch deploy add_job_status_field
```

### 2. Update Environment Variables

Update your `.env` file with poller configuration:

```bash
# Copy from .env.example if needed
cp .env.example .env

# Edit .env to add poller settings
POLL_INTERVAL_MINUTES=5
JOB_REVIEW_QUEUE_NAME=job_review
```

### 3. Start Services

The poller service is defined in `docker-compose.yml` as the `poller` service:

```bash
# Start all services including poller
docker-compose up -d

# Or start just the poller service
docker-compose up -d poller

# Start worker to process enqueued jobs
docker-compose up -d worker
```

### 4. Verify Operation

Check the logs to ensure the poller is working:

```bash
# View poller logs
docker-compose logs -f poller

# Expected output:
# poller_1 | Starting poller daemon...
# poller_1 | Environment: development  
# poller_1 | Poll interval: 5 minutes
# poller_1 | Poller daemon initialized successfully
# poller_1 | Starting poller service - poll interval: 5 minutes
```

## Monitoring

### Log Events

The poller generates these log events:

- **Startup**: Service initialization and configuration
- **Poll Cycles**: Number of jobs found and processed each cycle
- **Job Processing**: Detailed logs for each job enqueued
- **Status Updates**: Confirmation of database status changes
- **Errors**: Any failures in polling, enqueueing, or status updates

### Example Log Output

```
2025-01-25 10:00:00 | INFO | Starting poll cycle for pending review jobs
2025-01-25 10:00:00 | INFO | Found 3 jobs pending review  
2025-01-25 10:00:00 | INFO | Job enqueued successfully - job_id: 12345678-1234-1234-1234-123456789abc, title: 'Senior Python Developer', company: Tech Corp, site: indeed, task_id: abc123
2025-01-25 10:00:00 | INFO | Poll cycle complete: 3 jobs enqueued for review
```

## Integration with Job Review Pipeline

The poller enqueues jobs to the `job_review` Redis queue where they are processed by workers running the `process_job_review` function. This function can be extended to integrate with:

- CrewAI job fit review services
- ML-based job matching algorithms  
- External API calls for job analysis
- Notification systems for job matches

## Troubleshooting

### Common Issues

1. **No jobs being processed**
   - Check if jobs table has records with `status='pending_review'`
   - Verify database connection and migration is applied
   - Check poller service logs for errors

2. **Jobs not updating status**
   - Verify database write permissions
   - Check for database constraint violations
   - Review error logs for SQL issues

3. **Redis connection issues**
   - Ensure Redis service is running
   - Verify Redis connection parameters
   - Check network connectivity between services

### Health Checks

```bash
# Check poller service status
docker-compose ps poller

# Check Redis queue status  
docker-compose exec redis redis-cli LLEN job_review

# Check database for pending jobs
docker-compose exec db psql -U trainium_user -d trainium -c "SELECT COUNT(*) FROM jobs WHERE status='pending_review';"
```

## Testing

### Unit Tests

Run the poller unit tests:

```bash
# From repository root
python -m pytest tests/services/infrastructure/test_poller.py -v
```

### Manual Testing

1. **Insert test job**:
   ```sql
   INSERT INTO jobs (site, job_url, title, company, status) 
   VALUES ('test', 'https://example.com/test', 'Test Job', 'Test Company', 'pending_review');
   ```

2. **Watch poller logs**:
   ```bash
   docker-compose logs -f poller
   ```

3. **Verify job status change**:
   ```sql
   SELECT id, title, company, status, updated_at FROM jobs WHERE title = 'Test Job';
   ```

## Performance

- **Polling Frequency**: Default 5-minute interval balances responsiveness with database load
- **Batch Processing**: Processes up to 100 jobs per cycle to manage memory usage
- **Database Indexes**: Optimized queries use indexes on `status` and `updated_at` fields
- **Connection Pooling**: Uses asyncpg connection pooling for efficient database access

## Security

- **SQL Injection**: All queries use parameterized statements
- **Access Control**: Inherits database permissions from application configuration
- **Resource Limits**: Container resource limits prevent memory/CPU exhaustion
- **Error Handling**: Sensitive data not exposed in error messages

## Future Enhancements

- **Priority Queuing**: Support for high-priority job processing
- **Retry Logic**: Automatic retry of failed enqueue operations
- **Metrics Collection**: Integration with monitoring systems (Prometheus, etc.)
- **Dynamic Polling**: Adjust poll frequency based on job volume
- **Multi-tenant Support**: Separate queues per user or organization