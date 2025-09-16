# JobSpy Pagination & Schedule Fix

## Issue Addressed
The original implementation had two critical problems:
1. **Pagination only working with explicit `enable_pagination=True`** - Users reported still getting only 25 jobs
2. **Schedules disabled by default** - Historic schedules were not running because they were created with `enabled=false`

## Root Cause Analysis

### Problem 1: Pagination Logic Flaw  
The original logic required BOTH conditions to be true:
```python
# FLAWED LOGIC - required both conditions
if enable_pagination and max_results_target > 25:
    return _scrape_jobs_paginated(...)
```

This meant that even if `results_wanted=100`, pagination would NOT trigger unless `enable_pagination=True` was explicitly set.

### Problem 2: Disabled Schedules
The database migration created schedules with `enabled=false` by default:
```sql
INSERT INTO site_schedules (site_name, enabled, ...) VALUES 
    ('indeed', false, ...),  -- Disabled!
    ('linkedin', false, ...), -- Disabled!
```

## Fixes Applied

### Fix 1: Auto-Enable Pagination Logic
**File**: `app/services/jobspy/scraping.py`

```python
# NEW LOGIC - Auto-enable pagination for high volume requests
enable_pagination = payload.get("enable_pagination", False)
max_results_target = payload.get("max_results_target", payload.get("results_wanted", 15))

# Auto-enable pagination if results_wanted > 25, even if not explicitly enabled
if max_results_target > 25:
    enable_pagination = True
    logger.info(f"Auto-enabling pagination for {max_results_target} results (exceeds 25-result limit)")

# Now pagination triggers automatically for high-volume requests
if enable_pagination and max_results_target > 25:
    return _scrape_jobs_paginated(...)
```

### Fix 2: Enhanced Scheduler Auto-Enable
**File**: `app/services/infrastructure/scheduler.py`

```python
# Enhanced scheduler logic with better logging
results_wanted = payload.get("results_wanted", 15)
if results_wanted > 25:
    payload["enable_pagination"] = True
    payload["max_results_target"] = results_wanted
    logger.info(f"Auto-enabled pagination for {site_name} - target: {results_wanted} results")
```

### Fix 3: Enable Schedules Script
**File**: `enable_schedules.py`

Provides a script to enable schedules with proper high-volume configuration:
- Indeed: 100 results (triggers pagination)
- LinkedIn: 75 results (triggers pagination)  
- Glassdoor: 50 results (triggers pagination)

### Fix 4: Database Update Script
**File**: `fix_schedules.sql`

SQL script to directly update the database with enabled schedules and proper pagination configuration.

## Testing

### Automated Tests
Run `python test_pagination_fix.py` to verify:
- ✅ results_wanted > 25 automatically enables pagination
- ✅ Scheduler properly configures pagination parameters
- ✅ All edge cases handled correctly

### Manual Testing  
Run `python manual_scrape_test.py` to test actual scraping (requires dependencies).

## Expected Behavior After Fix

### Before Fix:
- `{"results_wanted": 50}` → Returns ~25 jobs (no pagination)
- Schedules don't run (disabled by default)

### After Fix:
- `{"results_wanted": 50}` → Returns ~50-150 jobs (auto-pagination enabled)
- Schedules run on configured intervals with high-volume results

## Deployment Steps

1. **Apply the code changes** (already in this commit)
2. **Enable schedules** (choose one):
   - Option A: Run `python enable_schedules.py` (requires app dependencies)
   - Option B: Execute `fix_schedules.sql` directly on database
3. **Restart services**:
   - `docker-compose restart scheduler`
   - `docker-compose restart worker`
4. **Monitor logs** for pagination activity:
   - Look for "Auto-enabling pagination" messages
   - Verify batch processing with multiple time windows

## Verification

After deployment, you should see in the logs:
```
Auto-enabling pagination for 100 results (exceeds 25-result limit)
Pagination mode active - targeting 100 results
Batch 1: Scraping jobs from last 24 hours
Batch 1: Found 45 jobs, 42 new unique jobs
Batch 2: Scraping jobs from last 72 hours
...
```

And schedules running:
```
✅ Successfully enqueued scheduled job for indeed - target: 100 results
📊 Queue status: 3 pending, 12 completed, 0 failed
```

## Files Modified

- `app/services/jobspy/scraping.py` - Fixed auto-enable pagination logic
- `app/services/infrastructure/scheduler.py` - Enhanced scheduler parameter handling
- `enable_schedules.py` - Script to enable and configure schedules  
- `fix_schedules.sql` - Direct database update script
- `test_pagination_fix.py` - Comprehensive test suite
- `manual_scrape_test.py` - Manual testing script

This fix ensures that pagination works automatically for any request with `results_wanted > 25`, and that schedules are properly enabled and configured for high-volume job collection.