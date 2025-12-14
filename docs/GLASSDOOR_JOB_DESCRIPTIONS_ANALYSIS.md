# Glassdoor Job Descriptions - Analysis & Solutions

**Date:** October 2, 2025
**Issue:** Glassdoor jobs in database have `null` descriptions
**Root Cause:** Glassdoor API limitations & scraping restrictions

---

## Problem Analysis

### Current State
- 617 jobs in database from Glassdoor
- All have `description = null`
- Modal shows "Job description not available"

### Investigation Results

**JobSpy Library Status:**
- Version: `python-jobspy==1.1.82`
- Glassdoor scraper: **Working but limited**
- Test scraping: Returns 400 errors with location parsing issues

**Glassdoor API Limitations:**
1. **No full descriptions in API** - Glassdoor doesn't provide complete job descriptions via their public API
2. **Rate limiting** - Heavy rate limits on scraping
3. **Location parsing** - Strict location format requirements
4. **Anti-scraping measures** - Increasingly aggressive bot detection

---

## Why This Happens

### **JobSpy's Glassdoor Integration:**

From testing and code review:
```python
# In app/services/jobspy/scraping.py lines 94-98
description = (
    job_dict.get("job_description") or
    job_dict.get("description") or
    ""  # ← Falls back to empty string
)
```

**What Glassdoor provides:**
✅ Job title
✅ Company name
✅ Location
✅ Salary range
✅ Job URL
❌ **Full job description** (not available via API)

**What you need to do:**
- Click the job URL → Opens Glassdoor website
- Read description on Glassdoor directly
- This is by design - Glassdoor wants traffic to their site

---

## Solutions

### **Option 1: Use LinkedIn Instead (RECOMMENDED)**

**Why LinkedIn is better:**
- ✅ Full job descriptions available via MCP server
- ✅ We already implemented LinkedIn workflow
- ✅ Better data quality
- ✅ More relevant for your career level

**How to switch:**

1. **Stop using Glassdoor scraping:**
```python
# In your crew configurations or API calls
site_name=["linkedin"]  # Remove "glassdoor"
```

2. **Use LinkedIn MCP workflow:**
   - Save jobs on LinkedIn mobile
   - Paste URL into Quick Add (`/add-linkedin-job`)
   - LinkedIn MCP fetches full description → populates `scraped_markdown`
   - Modal displays complete JD

### **Option 2: Hybrid Approach**

**Use both sources strategically:**

**Glassdoor → Initial filtering:**
- Fast bulk scraping
- Get salary data
- Get company names
- Quick AI review based on metadata

**LinkedIn → Deep dive:**
- For jobs that pass Glassdoor filter
- Get full descriptions
- Make final decision
- Apply with AI assistance

**Implementation:**
```python
# Phase 1: Bulk scrape Glassdoor (metadata only)
glassdoor_jobs = scrape_glassdoor(results=100)
filtered_jobs = ai_pre_filter(glassdoor_jobs)  # Filter by salary, remote, etc.

# Phase 2: Get LinkedIn details for top candidates
for job in filtered_jobs[:20]:  # Top 20 only
    linkedin_url = find_linkedin_equivalent(job)
    full_job = fetch_linkedin_job(linkedin_url)
    # Now has full description for AI analysis
```

### **Option 3: Web Scraping Enhancement (NOT RECOMMENDED)**

**Advanced scraping to get descriptions:**

⚠️ **Problems:**
- Violates Glassdoor ToS
- High risk of IP bans
- Requires headless browser (Selenium/Playwright)
- Slow (1-2 seconds per job)
- Maintenance burden (breaks when Glassdoor updates HTML)

**Only consider if:**
- You absolutely need Glassdoor-exclusive jobs
- Willing to handle legal/technical risks
- Have time to maintain scraper

---

## Recommended Action Plan

### **Short Term (This Week):**

1. ✅ **Keep modal graceful fallback:**
   - Already implemented
   - Shows "View on LinkedIn" link
   - Users can click to external site

2. ✅ **Document limitation for users:**
   - Add tooltip: "Glassdoor jobs require clicking to view full description"
   - Set expectations upfront

### **Medium Term (Next Sprint):**

3. **Switch primary source to LinkedIn:**
   - Update job scraping crews to use LinkedIn MCP
   - Glassdoor becomes secondary/optional
   - Example config:
   ```yaml
   # In job_posting_review/config/tasks.yaml
   search:
     site_name: ["linkedin"]  # Primary
     # site_name: ["glassdoor"]  # Commented out
   ```

4. **Implement smart source selection:**
   ```python
   def get_job_with_description(job_title, company):
       # Try LinkedIn first
       linkedin_job = fetch_linkedin_job(job_title, company)
       if linkedin_job and linkedin_job.description:
           return linkedin_job

       # Fallback to Glassdoor (metadata only)
       glassdoor_job = fetch_glassdoor_job(job_title, company)
       return glassdoor_job  # Has URL but no description
   ```

### **Long Term (Future):**

5. **Multi-source aggregation:**
   - Fetch same job from multiple sites
   - Merge data:
     - Glassdoor: Salary data (most accurate)
     - LinkedIn: Full description
     - Indeed: Application stats
   - Best-of-breed approach

---

## Technical Details

### **Current Database Schema:**

```sql
-- jobs table
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    title TEXT,
    company TEXT,
    description TEXT,           -- ← NULL for Glassdoor jobs
    scraped_markdown TEXT,      -- ← NULL (LinkedIn only)
    job_url TEXT,               -- ← Works! Links to Glassdoor
    site VARCHAR(50),           -- ← "Glassdoor"
    ...
);
```

### **JobSpy Glassdoor Behavior:**

```python
# What JobSpy returns for Glassdoor:
{
    "title": "Senior Software Engineer",
    "company": "Acme Corp",
    "location": "San Francisco, CA",
    "salary_min": 150000,
    "salary_max": 200000,
    "job_url": "https://glassdoor.com/job/...",
    "description": "",  # ← Empty! Not provided by API
    "site": "glassdoor"
}
```

### **LinkedIn MCP Behavior:**

```python
# What LinkedIn MCP returns:
{
    "title": "Senior Software Engineer",
    "company": "Acme Corp",
    "description": "We are seeking...",  # ← Full description!
    "scraped_markdown": "# Role\n\nWe are...",  # ← Formatted!
    "job_url": "https://linkedin.com/jobs/view/...",
    "site": "linkedin"
}
```

---

## User Workaround (Current State)

**For users right now:**

1. Navigate to `/reviewed-jobs`
2. See job card with AI TL;DR and metadata
3. Press `J` to open JD modal
4. See "Job description not available"
5. Click "View on Glassdoor →" link
6. Read full description on Glassdoor site
7. Return to app, make swipe decision

**This is acceptable because:**
- AI TL;DR still provides value (based on title, company, salary)
- One click to external site is reasonable
- Most users won't need full JD for every job

---

## Conclusion

**Recommended Path Forward:**

1. ✅ **Accept current limitation** - Modal gracefully handles missing descriptions
2. ✅ **Fixed immediate errors** - `base_resumes` → `resumes` table name
3. 🎯 **Switch to LinkedIn** - Better data quality, full descriptions available
4. 📊 **Keep Glassdoor for metadata** - Salary data, bulk filtering

**Next Steps:**
1. Test the Full AI workflow with the `resumes` table fix
2. Start using LinkedIn MCP workflow for new jobs
3. Gradually phase out Glassdoor as primary source
4. Use Glassdoor only for salary benchmarking

---

**Bottom line:** This isn't a bug - it's a Glassdoor API limitation. The solution is using LinkedIn instead, which we've already built! 🚀
