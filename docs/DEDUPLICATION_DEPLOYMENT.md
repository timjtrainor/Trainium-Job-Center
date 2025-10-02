# Deduplication System Deployment Guide

## ✅ Status: DEPLOYED

The advanced deduplication system is now **fully deployed** and ready to use!

---

## What Was Deployed

### 1. ✅ Database Migrations
- **Indexes**: `idx_jobs_canonical_key`, `idx_jobs_fingerprint`, `idx_jobs_canonical_fingerprint`
- **View**: `jobs_deduplicated` for querying unique jobs
- **Deployment method**: Direct Docker exec (bypassed Sqitch connection issues)

### 2. ✅ Code Changes
- **Company Normalization**: [company_normalization.py](../python-service/app/services/infrastructure/company_normalization.py)
- **Job Persistence**: Updated [job_persistence.py](../python-service/app/services/infrastructure/job_persistence.py)
- **Tests**: Comprehensive test suite with 18/18 passing

### 3. ✅ Documentation
- **Full Guide**: [ADVANCED_DEDUPLICATION.md](ADVANCED_DEDUPLICATION.md)
- **Deployment Script**: [deploy_migrations.sh](../DB%20Scripts/deploy_migrations.sh)

---

## Connection Issue Resolved

### The Problem
```bash
# This failed:
sqitch deploy
# Error: connection to server on socket "/tmp/.s.PGSQL.5432" failed
```

### The Solution
Your PostgreSQL runs in **Docker on port 5434**, not locally on 5432. Use Docker exec instead:

```bash
# Deploy via Docker (this worked!)
cat "migration.sql" | docker exec -i trainium_db psql -U trainium_user -d trainium
```

### Easy Deployment Script
```bash
# Use the deployment helper script
cd "DB Scripts"
./deploy_migrations.sh
```

---

## Current Database Status

### Jobs Table
- **Total jobs**: 241
- **Canonical keys**: 0 (old jobs scraped before deduplication)
- **Next scrapes**: Will automatically get canonical keys + fingerprints

### Indexes Created ✅
```sql
idx_jobs_canonical_key          -- Fast lookup by company+title
idx_jobs_fingerprint            -- Fast lookup by content hash
idx_jobs_canonical_fingerprint  -- Combined lookup
```

### View Created ✅
```sql
jobs_deduplicated  -- Shows only unique jobs (deduped)
```

---

## Verification Steps

### 1. Check Indexes
```bash
docker exec -i trainium_db psql -U trainium_user -d trainium -c "
  SELECT indexname FROM pg_indexes
  WHERE tablename = 'jobs'
  AND indexname LIKE '%canonical%' OR indexname LIKE '%fingerprint%';
"
```

**Expected Output**:
```
idx_jobs_canonical_key
idx_jobs_fingerprint
idx_jobs_canonical_fingerprint
```

### 2. Check View
```bash
docker exec -i trainium_db psql -U trainium_user -d trainium -c "
  SELECT COUNT(*) FROM jobs_deduplicated;
"
```

### 3. Query Deduplicated Jobs
```bash
docker exec -i trainium_db psql -U trainium_user -d trainium << 'EOF'
SELECT
    title,
    company,
    found_on_sites,
    duplicate_count
FROM jobs_deduplicated
LIMIT 5;
EOF
```

---

## Next Steps

### 1. Restart Python Service (Optional - for new scrapes)
```bash
# If you have the service running, restart it to load the new code
cd python-service
# Stop current service (if running)
# Start again - jobs will now get canonical_key + fingerprint
```

### 2. Test with New Scrapes

The deduplication will work automatically on **new scrapes**:

```bash
# Trigger a scrape (via API or UI)
# New jobs will automatically get:
# - canonical_key (e.g., "amazon_senior_product_manager")
# - fingerprint (content hash)
```

### 3. Backfill Existing Jobs (Optional)

If you want to deduplicate your existing 241 jobs, run this migration:

```sql
-- Backfill canonical keys for existing jobs
UPDATE jobs
SET
    canonical_key = generate_canonical_key(title, company),
    fingerprint = generate_fingerprint(description, title, company)
WHERE canonical_key IS NULL;
```

**Note**: You'll need to create the `generate_canonical_key()` and `generate_fingerprint()` SQL functions first, or run a Python script to do this.

---

## Usage Examples

### Query Deduplicated Jobs
```sql
-- Get unique PM jobs from last 7 days with salary >= $180k
SELECT
    title,
    company,
    min_amount,
    max_amount,
    is_remote,
    date_posted,
    found_on_sites,       -- Shows all sites where job appeared
    duplicate_count,      -- How many times it was found
    all_urls             -- All job URLs across sites
FROM jobs_deduplicated
WHERE date_posted > NOW() - INTERVAL '7 days'
AND (min_amount >= 180000 OR min_amount IS NULL)
AND title ILIKE '%product manager%'
ORDER BY date_posted DESC;
```

### Check Deduplication Stats
```bash
docker exec -i trainium_db psql -U trainium_user -d trainium << 'EOF'
SELECT
    COUNT(*) as total_jobs,
    COUNT(DISTINCT canonical_key) as unique_by_canonical_key,
    COUNT(*) - COUNT(DISTINCT COALESCE(canonical_key, id::text)) as duplicates_eliminated,
    ROUND(100.0 * (COUNT(*) - COUNT(DISTINCT COALESCE(canonical_key, id::text))) / COUNT(*), 2) as dedup_percentage
FROM jobs
WHERE canonical_key IS NOT NULL;
EOF
```

### Find Duplicate Jobs
```bash
docker exec -i trainium_db psql -U trainium_user -d trainium << 'EOF'
-- Show jobs with duplicates across sites
SELECT
    canonical_key,
    COUNT(*) as duplicate_count,
    ARRAY_AGG(DISTINCT site) as found_on_sites,
    ARRAY_AGG(title) as title_variations,
    ARRAY_AGG(company) as company_variations
FROM jobs
WHERE canonical_key IS NOT NULL
GROUP BY canonical_key
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
LIMIT 10;
EOF
```

---

## Troubleshooting

### Issue: Sqitch won't connect

**Solution**: Use Docker exec instead
```bash
# Don't use Sqitch directly - use the helper script
cd "DB Scripts"
./deploy_migrations.sh
```

### Issue: Jobs don't have canonical_key

**Cause**: Old jobs scraped before deduplication was deployed

**Solution**:
1. New scrapes will automatically get canonical keys
2. Or backfill existing jobs (see above)

### Issue: View returns no results

**Check if view exists**:
```bash
docker exec -i trainium_db psql -U trainium_user -d trainium -c "\dv jobs_deduplicated"
```

**If missing, redeploy**:
```bash
cd "DB Scripts"
cat sqitch/deploy/jobs_deduplicated_view.sql | docker exec -i trainium_db psql -U trainium_user -d trainium
```

---

## File Locations

### Database
- **Indexes**: `DB Scripts/sqitch/deploy/jobs_deduplication_indexes.sql`
- **View**: `DB Scripts/sqitch/deploy/jobs_deduplicated_view.sql`
- **Deploy Script**: `DB Scripts/deploy_migrations.sh`

### Python Code
- **Company Normalizer**: `python-service/app/services/infrastructure/company_normalization.py`
- **Job Persistence**: `python-service/app/services/infrastructure/job_persistence.py`

### Documentation
- **This Guide**: `docs/DEDUPLICATION_DEPLOYMENT.md`
- **Full Details**: `docs/ADVANCED_DEDUPLICATION.md`

---

## Docker Commands Reference

### Connect to PostgreSQL
```bash
docker exec -it trainium_db psql -U trainium_user -d trainium
```

### Run SQL File
```bash
cat migration.sql | docker exec -i trainium_db psql -U trainium_user -d trainium
```

### Check Container Status
```bash
docker ps | grep trainium_db
```

### View Container Logs
```bash
docker logs trainium_db
```

---

## Summary

✅ **Database migrations deployed successfully**
✅ **Indexes created for fast deduplication queries**
✅ **View ready for job review workflow**
✅ **Python code updated to generate canonical keys**
✅ **Tests passing (18/18)**

**Ready to use!** Your next job scrapes will automatically be deduplicated across Indeed, Glassdoor, and other sites, with proper handling of Amazon/AWS, Microsoft/Azure, Google/Alphabet, and 30+ other major companies.
