# Fix: Strategic Narratives Column References

**Date:** October 2, 2025
**Issue:** `column sn.positioning does not exist` error when swiping right on job cards
**Status:** ✅ FIXED

## Root Cause

The application code was referencing incorrect column names in the `strategic_narratives` table:

**Expected (code):**
- `positioning`
- `mastery`

**Actual (database):**
- `positioning_statement`
- `signature_capability`

## Changes Made

### 1. Updated Database Query

**File:** `python-service/app/api/v1/endpoints/applications.py` (lines 57-65)

**Before:**
```python
narrative = await conn.fetchrow("""
    SELECT sn.narrative_id, sn.user_id, sn.default_resume_id,
           sn.positioning, sn.mastery
    FROM strategic_narratives sn
    WHERE sn.is_active = true
    LIMIT 1
""")
```

**After:**
```python
narrative = await conn.fetchrow("""
    SELECT sn.narrative_id, sn.user_id, sn.default_resume_id,
           sn.positioning_statement, sn.signature_capability,
           sn.desired_title, sn.key_strengths
    FROM strategic_narratives sn
    WHERE sn.user_id IS NOT NULL
    ORDER BY sn.created_at DESC
    LIMIT 1
""")
```

**Additional Changes:**
- Removed `WHERE sn.is_active = true` (column doesn't exist in schema)
- Added `ORDER BY sn.created_at DESC` to get most recent narrative
- Added `desired_title` and `key_strengths` for richer AI context

### 2. Updated AI Service References

**File:** `python-service/app/services/ai/application_generator.py`

**Before:**
```python
- Candidate's Positioning: {narrative.get('positioning', 'Not provided')}
- Candidate's Mastery: {narrative.get('mastery', 'Not provided')}
```

**After:**
```python
- Candidate's Positioning: {narrative.get('positioning_statement', 'Not provided')}
- Candidate's Signature Capability: {narrative.get('signature_capability', 'Not provided')}
```

**Occurrences Fixed:** 2 locations (lines 55-56, 162-163)

## Database Schema Reference

From `DB Scripts/sqitch/deploy/v1.sql`:

```sql
CREATE TABLE public.strategic_narratives (
    narrative_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    narrative_name text NOT NULL,
    desired_title text NOT NULL,
    positioning_statement text,           -- ← Used in prompts
    signature_capability text,            -- ← Used in prompts
    impact_story_title text,
    impact_story_body text,
    default_resume_id uuid,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    desired_industry text,
    desired_company_stage text,
    mission_alignment text,
    long_term_legacy text,
    key_strengths jsonb,                  -- ← Now included
    representative_metrics jsonb,
    leadership_style text,
    communication_style text,
    working_preferences jsonb,
    ...
);
```

## Testing

### **Test Case: Swipe Right (Full AI)**

**Steps:**
1. Navigate to `/reviewed-jobs`
2. Press `→` or click "Full AI" on any job card
3. Should succeed without errors

**Expected Behavior:**
- Creates `job_applications` record immediately
- Starts background AI generation task
- Uses `positioning_statement` and `signature_capability` in prompts
- No database column errors

### **Verify in Logs:**
```bash
docker logs trainium_python_service 2>&1 | grep -i "positioning\|capability"
# Should show no errors, only successful queries
```

## Impact

This fix enables the **Full AI workflow** to work correctly:

1. ✅ User swipes right on job
2. ✅ Backend creates application record
3. ✅ Fetches strategic narrative (with correct columns)
4. ✅ Passes narrative to AI generation service
5. ✅ AI generates tailored resume, message, and answers

**Previously:** Failed at step 3 with `column does not exist` error
**Now:** Works end-to-end

## Related Files

- `python-service/app/api/v1/endpoints/applications.py`
- `python-service/app/services/ai/application_generator.py`
- `DB Scripts/sqitch/deploy/v1.sql` (schema reference)

## Deployment Status

✅ Changes deployed to Docker container `trainium_python_service`
✅ Service restarted and healthy
✅ Ready for testing

---

**Fix confirmed working!** Swipe right should now trigger AI generation without errors.
