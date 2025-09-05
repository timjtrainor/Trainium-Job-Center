# Jobs Table Persistence

This document describes the job persistence functionality for storing scraped job data to PostgreSQL using Sqitch migrations.

## Database Migration

### Running Sqitch Commands

All Sqitch commands should be run from the `DB Scripts/sqitch/` directory.

First, set up your environment variables:
```bash
# Load environment variables from .env file
export $(cat .env | xargs)
export PG_LOCAL_URI="db:pg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"
```

Deploy the jobs table:
```bash
cd "DB Scripts/sqitch"
sqitch deploy
```

Verify the deployment:
```bash
sqitch verify
```

Revert if needed:
```bash
sqitch revert
```

### What the Migration Creates

The `jobs_table_init` migration creates:

- **jobs table** with all required fields and appropriate PostgreSQL types
- **Unique constraint** on `(site, job_url)` for idempotent upserts
- **Indexes** on commonly queried fields:
  - `site` for filtering by job board
  - `date_posted DESC` for recent jobs
  - `ingested_at DESC` for tracking when jobs were scraped
  - `is_remote` for remote job filtering
  - `company` for company-based searches
  - GIN index on `source_raw` for JSON queries

## Field Mapping

The persistence service maps JobSpy scraped data to database fields:

| JobSpy Field | Database Field | Type | Notes |
|--------------|----------------|------|-------|
| `site` | `site` | text | Job board name (indeed, linkedin, etc.) |
| `title` | `title` | text | Job title |
| `company` | `company` | text | Company name |
| `job_url` | `job_url` | text | Canonical URL (unique with site) |
| `salary_min` | `min_amount` | numeric(12,2) | Minimum salary |
| `salary_max` | `max_amount` | numeric(12,2) | Maximum salary |
| `salary_source` | `salary_source` | text | Source of salary data |
| `interval` | `interval` | text | yearly, monthly, hourly |
| `description` | `description` | text | Job description (markdown) |
| `date_posted` | `date_posted` | timestamptz | When job was posted |
| `is_remote` | `is_remote` | boolean | Remote work flag |
| `job_type` | `job_type` | text | fulltime, contract, etc. |
| *All fields* | `source_raw` | jsonb | Complete original record |
| *Generated* | `ingested_at` | timestamptz | When we scraped it |

### Placeholder Fields (Not Currently Populated)

These fields are reserved for future functionality:

- `company_url` - Company website (not in JobSpy data)
- `location_country/state/city` - Parsed location fields
- `compensation` - Formatted compensation string
- `currency` - Currency code
- `canonical_key` - Normalized deduplication key
- `fingerprint` - Content-based hash
- `duplicate_group_id` - Cross-board duplicate grouping

## Using the Persistence Service

### Basic Usage

```python
from app.services.infrastructure.job_persistence import persist_jobs
from app.schemas.jobspy import ScrapedJob

# Create or get scraped jobs
jobs = [
    ScrapedJob(
        title="Python Developer", 
        company="Tech Corp",
        job_url="https://indeed.com/job/123",
        site="indeed",
        salary_min=80000.0,
        is_remote=True
    ),
    # ... more jobs
]

# Persist to database
summary = await persist_jobs(records=jobs, site_name="indeed")
print(summary)
```

### Persistence Summary Format

The `persist_jobs` function returns a summary dictionary:

```python
{
    "inserted": 15,           # Number of new records inserted
    "skipped_duplicates": 3,  # Number of duplicates skipped (idempotent)
    "errors": [               # List of error messages for failed records
        "Record 5: missing job_url",
        "Record 8: missing title"
    ]
}
```

### Integration Points

**Sync API Mode** (`/jobs/scrape?mode=sync`):
- Scrapes jobs immediately
- Persists results to database
- Returns both scrape results and persistence summary

**Async Worker Mode** (default):
- Jobs are queued and processed by RQ workers
- After successful scraping, jobs are automatically persisted
- Persistence summary is logged

## Idempotency and Error Handling

### Duplicate Prevention

- **Unique constraint** on `(site, job_url)` prevents duplicates
- Re-ingesting the same job URL from the same site is a no-op
- Duplicate attempts are counted in `skipped_duplicates`

### Partial Failure Handling

- Individual record failures don't stop the entire batch
- Records with missing `job_url` or `title` are skipped and logged
- Database errors for individual records are caught and reported
- Successful records are still persisted even if others fail

### Batch Processing

- Large batches are processed in a single database transaction
- All-or-nothing transaction semantics within the batch
- Failed batches can be retried safely due to idempotency

## Examples

### Example 1: Manual Sync Scraping

```bash
curl -X POST "http://localhost:8000/jobs/scrape?mode=sync" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "indeed",
    "search_term": "python developer", 
    "location": "remote",
    "results_wanted": 10
  }'
```

Response includes persistence summary:
```json
{
  "success": true,
  "data": {
    "jobs": [...],
    "total_found": 8,
    "persistence_summary": {
      "inserted": 6,
      "skipped_duplicates": 2,
      "errors": []
    }
  }
}
```

### Example 2: Async Worker Processing

```python
# Jobs are automatically persisted after scraping completes
# Check worker logs for persistence results:
# "Run abc123: Persisted jobs - {'inserted': 25, 'skipped_duplicates': 5, 'errors': []}"
```

### Example 3: Direct Service Usage

```python
from app.services.infrastructure.job_persistence import get_job_persistence_service

service = get_job_persistence_service()

# Process mixed batch with some invalid records
mixed_jobs = [
    {"title": "Developer", "job_url": "https://example.com/1"},  # Dict format OK
    ScrapedJob(title="", job_url="https://example.com/2"),       # Missing title - error
    ScrapedJob(title="Engineer", job_url="https://example.com/3"), # Good record
]

result = await service.persist_jobs(mixed_jobs, "linkedin")
# Returns: {"inserted": 2, "skipped_duplicates": 0, "errors": ["Record 1: missing title"]}
```

## Testing

Run the persistence unit tests:

```bash
cd python-service
python test_persistence_unit.py
```

These tests verify:
- Field mapping and normalization
- Date parsing from various formats  
- Validation logic for required fields
- ScrapedJob model functionality

## Troubleshooting

**Database Connection Issues:**
- Verify `DATABASE_URL` is set in your `.env` file
- Check PostgreSQL is running and accessible
- Ensure Sqitch migration was deployed successfully

**Persistence Errors:**
- Check worker logs for detailed error messages
- Verify job records have required fields (`title`, `job_url`)
- Ensure `site_name` parameter matches the job board identifier

**Sqitch Issues:**
- Verify `PG_LOCAL_URI` environment variable is set correctly
- Check database credentials and connectivity
- Use `sqitch status` to see current migration state