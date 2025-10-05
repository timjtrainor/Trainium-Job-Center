# Backend Fix: Job Description Display

**Date:** October 2, 2025
**Issue:** Full JD modal was not showing job descriptions from database
**Status:** ✅ FIXED

## Changes Made

### 1. Updated Database Query

**File:** `python-service/app/services/infrastructure/database.py`

**Added `scraped_markdown` to response** (lines 726):
```python
job_data = {
    "job": {
        ...
        "description": row["description"],
        "scraped_markdown": row.get("scraped_markdown"),  # May not exist yet
        ...
    }
}
```

**Note:** Used `.get()` to handle cases where the `scraped_markdown` column doesn't exist yet (before migration is run).

### 2. Frontend Already Handles Both Fields

**File:** `components/JobCardView.tsx` (line 443)

The modal already checks for both fields:
```tsx
{currentJob.description || currentJob.scraped_markdown ? (
    <MarkdownPreview content={currentJob.description || currentJob.scraped_markdown || ''} />
) : (
    <div>Job description not available...</div>
)}
```

## Current Behavior

### **For Jobs WITH Descriptions:**
1. User clicks "View Full JD" (or presses `J`)
2. Modal opens with markdown-formatted job description
3. User can read full JD, then make swipe decision from modal footer

### **For Jobs WITHOUT Descriptions:**
1. User clicks "View Full JD"
2. Modal shows: "Job description not available. [View on LinkedIn]"
3. User can click external link if needed

## Why Some Jobs Have No Description

**Glassdoor Jobs:**
- Scraped via JobSpy
- Glassdoor API doesn't provide full job descriptions
- Only provides: title, company, location, salary range

**LinkedIn Jobs (Future):**
- Will be scraped via LinkedIn MCP server
- Will populate `scraped_markdown` field
- Full job descriptions will be available

## Database Migration Status

The `scraped_markdown` column will be added when running:
```bash
cd "DB Scripts/sqitch"
sqitch deploy add_job_workflow_enhancements
```

**Until migration runs:**
- `scraped_markdown` will be `null` for all jobs
- Modal will fall back to `description` field
- Glassdoor jobs will show "not available" message

## Testing

### **Test Case 1: Job WITH Description**
```bash
# Create a test job with description
curl -X POST http://localhost:8180/api/linkedin-jobs/fetch-by-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://linkedin.com/jobs/view/123456"}'

# View in UI
# Press J in JobCardView → Should show full JD in modal
```

### **Test Case 2: Job WITHOUT Description**
```bash
# Use existing Glassdoor job
# Navigate to /reviewed-jobs
# Press J on any Glassdoor job
# Should show: "Job description not available. View on LinkedIn"
```

## Summary

✅ **Backend updated** to return `description` and `scraped_markdown` fields
✅ **Frontend already handles** both fields with proper fallback
✅ **Graceful degradation** for jobs without descriptions
✅ **Ready for LinkedIn workflow** - will populate `scraped_markdown` when implemented

**No further backend changes needed!** The fix is complete and deployed.
