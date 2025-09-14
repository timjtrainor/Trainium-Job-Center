# SQL Migrations

This directory contains raw SQL migration files for the Trainium Job Center database.

## Migration Files

### 001_create_job_reviews.sql
Creates the `job_reviews` table to store AI and human review results for job postings.

**Schema:**
- `id` (uuid, PK) - Primary key
- `job_id` (uuid, FK) - References jobs.id with CASCADE DELETE
- `ai_decision` (text) - AI decision: 'approve' or 'reject'
- `ai_reason` (text) - AI reasoning (supports text or JSON format)
- `human_decision` (text) - Human decision: 'approve', 'reject', or 'none' (default)
- `human_comment` (text) - Human reviewer comments
- `final_decision` (text) - Final decision: 'approve' or 'reject' (required)
- `reviewed_at` (timestamptz) - Review completion timestamp (default: now())
- `error_message` (text) - Error message for failed reviews (nullable)

**Constraints:**
- Unique constraint on `job_id` prevents duplicate reviews per job
- Foreign key to `jobs.id` with CASCADE DELETE ensures referential integrity
- CHECK constraints enforce valid enum values for decision fields
- Optimized indexes for common query patterns

## Usage

To apply migrations manually:

```sql
-- Ensure jobs table exists first
\i 'DB Scripts/sqitch/deploy/jobs_table_init.sql'

-- Apply job_reviews migration
\i 'db/sql/001_create_job_reviews.sql'
```

## Verification

The migration includes proper:
- ✅ Foreign key constraints with cascade delete
- ✅ Unique constraints to prevent duplicates
- ✅ CHECK constraints for data validation
- ✅ Optimized indexes for performance
- ✅ Proper column types and defaults