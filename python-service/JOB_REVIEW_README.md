# Job Review Worker Service

This document describes the job review worker service implementation for the Trainium Job Center, which addresses Issue #215.

## Overview

The job review worker service consumes jobs from a Redis queue, runs the CrewAI job_posting_review crew, and persists results into the database. It supports multiple concurrent workers, error handling, and retry logic.

## Architecture

```
Jobs Table (status: pending_review)
           ↓
    Job Review Queue (Redis)
           ↓
     Worker Processes
           ↓
   CrewAI Job Review
           ↓
   Job Reviews Table + Jobs Status Update
```

## Key Components

### 1. Database Schema

**jobs table** (existing, enhanced):
- Added `status` field: `pending_review`, `in_review`, `reviewed`, `error`
- Added `updated_at` timestamp

**job_reviews table** (new):
- Stores AI review results from CrewAI
- Includes recommendation, confidence, rationale
- Stores full crew output for debugging
- Tracks retry attempts and errors

### 2. Worker Function

**`process_job_review(job_id, max_retries=3)`**
- Fetches job details from database
- Runs CrewAI job_posting_review crew
- Persists results to job_reviews table
- Updates job status appropriately
- Handles errors with exponential backoff

### 3. Queue Management

**Enhanced QueueService**:
- Supports both scraping and review queues
- Batch job queuing capabilities
- Multiple worker support
- Queue monitoring and statistics

### 4. High-Level Service

**JobReviewService**:
- Orchestrates job review workflow
- Batch processing of pending jobs
- Statistics and monitoring
- Failed job re-queuing

## Usage

### 1. Command Line Interface

```bash
# Queue pending jobs for review
python job_review_cli.py queue --limit 50 --retries 3

# Check specific job status
python job_review_cli.py status <job_id>

# View system statistics
python job_review_cli.py stats

# Re-queue failed jobs
python job_review_cli.py requeue --retries 3

# Test single job review
python job_review_cli.py test <job_id>
```

### 2. REST API Endpoints

```http
POST /job-review/queue
GET  /job-review/status/{job_id}
GET  /job-review/stats
POST /job-review/requeue
POST /job-review/test/{job_id}
```

### 3. Worker Process

```bash
# Start worker processes (consumes from both queues)
python worker.py
```

### 4. Integration Testing

```bash
# Run integration tests
python integration_test_job_review.py

# Run unit tests
pytest tests/test_job_review_*.py
```

## Configuration

Environment variables for job review system:

```env
# Queue Configuration
JOB_REVIEW_QUEUE_NAME=job_review
JOB_REVIEW_BATCH_SIZE=20
JOB_REVIEW_MAX_RETRIES=3
JOB_REVIEW_RETRY_DELAY=300

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/trainium
```

## Database Setup

1. Apply the new migration:
```sql
-- Deploy the job_reviews table
\i 'DB Scripts/sqitch/deploy/job_reviews_table.sql'
```

2. Verify the schema:
```sql
-- Check tables exist
\d jobs
\d job_reviews
```

## Workflow

### Job Review Process

1. **Job Scraping**: Jobs are scraped and stored with `status='pending_review'`

2. **Queue Jobs**: Use CLI or API to queue pending jobs:
   ```bash
   python job_review_cli.py queue --limit 20
   ```

3. **Worker Processing**: Workers pick up jobs from the queue:
   - Update status to `in_review`
   - Fetch job details from database
   - Prepare job data for CrewAI
   - Run `job_posting_review` crew
   - Parse and store results
   - Update status to `reviewed` or `error`

4. **Error Handling**: Failed jobs are retried up to max attempts:
   - Network errors, timeouts, CrewAI failures
   - Exponential backoff between retries
   - Jobs exceeding max retries marked as `error`

5. **Monitoring**: Track progress with stats and status checks:
   ```bash
   python job_review_cli.py stats
   ```

### Multiple Workers

Multiple worker processes can run concurrently:

```bash
# Terminal 1
python worker.py

# Terminal 2  
python worker.py

# Terminal 3
python worker.py
```

Workers will automatically distribute the workload and can scale horizontally.

## Error Handling

The system handles various error conditions:

1. **CrewAI Failures**: Timeout, API errors, processing failures
2. **Database Errors**: Connection issues, constraint violations
3. **Network Issues**: Redis connection problems
4. **Data Issues**: Malformed job data, missing required fields

Error information is stored in the `job_reviews.error_message` field and jobs can be re-queued for retry.

## Monitoring

### Queue Status
```bash
python job_review_cli.py stats
```

### Job Status
```bash
python job_review_cli.py status <job_id>
```

### API Monitoring
```http
GET /job-review/stats
```

## Testing

### Unit Tests
```bash
pytest tests/test_job_review_service.py
pytest tests/test_job_review_worker.py
```

### Integration Tests
```bash
python integration_test_job_review.py
```

### Manual Testing
```bash
# Create and test a single job
python test_job_review.py

# Or just create a test job
python test_job_review.py create-job
```

## Performance Considerations

1. **Batch Processing**: Queue jobs in batches rather than individually
2. **Worker Scaling**: Add more workers to increase throughput
3. **Database Connections**: Pool connections efficiently
4. **Queue Management**: Monitor queue length and failed jobs
5. **Retry Strategy**: Balance between reliability and performance

## Troubleshooting

### Common Issues

1. **Jobs stuck in 'in_review'**: Worker crashed, restart workers
2. **High retry count**: Check CrewAI configuration and ChromaDB connectivity
3. **Queue not processing**: Verify Redis connection and worker processes
4. **Database errors**: Check connection string and table schema

### Debugging

1. **Enable debug logging**: Set `LOG_LEVEL=DEBUG`
2. **Check worker logs**: Monitor worker output for errors
3. **Inspect database**: Query job_reviews table for error details
4. **Queue inspection**: Use Redis CLI to inspect queue contents

## Future Enhancements

1. **Priority Queues**: Prioritize certain jobs for faster processing
2. **Scheduled Reviews**: Automatically queue jobs on schedule
3. **Webhooks**: Notify external systems when reviews complete
4. **Metrics Dashboard**: Web UI for monitoring and management
5. **Review Quality**: Track and improve review accuracy
6. **A/B Testing**: Test different CrewAI configurations