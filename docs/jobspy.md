# JobSpy Integration Documentation

## Overview

This document describes the JobSpy integration implementation, including limitations, workarounds, and best practices for reliable job scraping.

## JobSpy Library Information

- **Library**: `python-jobspy==1.1.82`
- **Purpose**: Job scraping from multiple job boards (Indeed, LinkedIn, Glassdoor, ZipRecruiter, Google)
- **Core Function**: `scrape_jobs()`

## Key Limitations

### 1. No Native Pagination Support

**Issue**: JobSpy does not support traditional pagination parameters (offset, page number, etc.)

**Current Behavior**: 
- Uses `results_wanted` parameter to control result count
- Maximum effective results per call: ~25-50 jobs (varies by site)
- No way to fetch "next page" of results

**Impact**: Limits scalability for large-scale job collection

### 2. Site-Specific Parameter Constraints

**Indeed/Glassdoor**:
- Requires `country_indeed` parameter
- Only one active filter: `hours_old` OR `{job_type, is_remote}` OR `easy_apply`

**LinkedIn**:
- Only one active filter: `hours_old` OR `easy_apply`
- `linkedin_fetch_description=True` significantly slows requests

**Google**:
- Ignores standard parameters (`search_term`, `location`, etc.)
- Only honors `google_search_term` parameter

### 3. Rate Limiting Sensitivity

**Issue**: Job sites actively detect and block automated requests

**Constraints**:
- Requires delays between requests (2-8 seconds recommended)
- Longer delays needed for batch operations
- IP-based blocking possible with aggressive scraping

## Implemented Solutions

### 1. Pagination Workarounds

**Strategy 1: Time Window Splitting**
```python
time_windows = [24, 72, 168, 720]  # 1 day, 3 days, 1 week, 1 month
```
- Splits requests by posting recency (`hours_old` parameter)
- Most effective method for getting diverse results
- Automatically enabled when `results_wanted > 25`

**Strategy 2: Location Variations**
```python
# If location="San Francisco, CA", also try:
# - "CA" (state-level)
# - "Remote"  
# - "Los Angeles, CA" (nearby major cities)
```
- Expands geographic search scope
- Secondary strategy when time windows are exhausted

**Usage**:
```python
payload = {
    "site_name": "indeed",
    "search_term": "software engineer",
    "location": "San Francisco, CA",
    "results_wanted": 100,  # > 25, triggers pagination
    "enable_pagination": True,
    "max_results_target": 100
}
```

### 2. Enhanced Deduplication

**Pre-Database Deduplication**:
- URL-based: Removes duplicate `job_url` entries
- Content-based: Fingerprints based on title + company + description

**Database-Level Deduplication**:
- Unique constraint: `(site, job_url)`
- Content fingerprinting for change detection
- Update detection: Modified jobs are updated, not skipped

**Deduplication Statistics**:
```json
{
    "original_count": 150,
    "unique_count": 87,
    "url_duplicates_removed": 45,
    "content_duplicates_removed": 18,
    "total_duplicates_removed": 63
}
```

### 3. Comprehensive Logging

**Scheduler Logging**:
- Pre-execution diagnostics (schedule details, lock status)
- Per-site processing with emojis for easy scanning
- Success/failure tracking with detailed error messages
- Performance metrics (duration, jobs enqueued)

**Scraping Logging**:
- Batch-by-batch progress for paginated requests
- Pause times between requests (anti-detection)
- Success rates and error tracking
- Deduplication statistics

**Example Log Output**:
```
2024-01-15 10:30:15 | INFO | Processing schedule for site: indeed (ID: abc123)
2024-01-15 10:30:15 | INFO | Acquired Redis lock for indeed: scrape_lock:indeed
2024-01-15 10:30:16 | INFO | Enabled pagination for indeed - target: 100 results
2024-01-15 10:30:16 | INFO | Batch 1: Scraping jobs from last 24 hours
2024-01-15 10:30:22 | INFO | Batch 1: Found 45 jobs, 42 new unique jobs
2024-01-15 10:30:25 | INFO | Inter-batch pause: 4.23s
2024-01-15 10:30:25 | INFO | Batch 2: Scraping jobs from last 72 hours
2024-01-15 10:30:31 | INFO | ✅ Successfully enqueued scheduled job for indeed
```

## Configuration Parameters

### Core Scraping Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `site_name` | str | "indeed" | Job board to scrape |
| `search_term` | str | - | Job search keywords |
| `location` | str | - | Geographic location |
| `results_wanted` | int | 15 | Base result count |
| `is_remote` | bool | false | Remote job filter |
| `job_type` | str | - | Employment type filter |

### Pagination Enhancement

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_pagination` | bool | false | Enable multi-batch scraping |
| `max_results_target` | int | - | Target total results |

**Auto-enable Rule**: Pagination automatically enables when `results_wanted > 25`

### Rate Limiting

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_pause` | int | 2 | Minimum seconds between requests |
| `max_pause` | int | 8 | Maximum seconds between requests |

**Batch Pauses**: Inter-batch delays are 2x longer than single-request pauses

## Best Practices

### 1. Scheduling Configuration

**Frequency Guidelines**:
- High-volume sites (Indeed, LinkedIn): 2-4 hours minimum
- Lower-volume sites: 1-2 hours acceptable
- Add ±10% jitter to prevent synchronized loads

**Payload Configuration**:
```json
{
    "site_name": "indeed",
    "search_term": "software engineer",
    "location": "San Francisco, CA",
    "results_wanted": 75,
    "country_indeed": "USA",
    "hours_old": 24,
    "enable_pagination": true
}
```

### 2. Error Handling

**Site Locks**: Prevent concurrent scraping of same site
- Redis locks with 30-minute timeout
- Database backup lock checking
- Automatic cleanup on completion

**Graceful Degradation**:
- Partial success when some batches fail
- Error logging without stopping entire job
- Retry logic with exponential backoff

### 3. Monitoring

**Key Metrics to Track**:
- Success rate per site
- Average jobs per scrape
- Deduplication effectiveness
- Processing time trends
- Error frequency patterns

**Alert Conditions**:
- Success rate < 50% for any site
- Zero jobs found consistently
- Processing time > 5 minutes
- High error rates (>25%)

## Troubleshooting

### Common Issues

**1. Zero Results Returned**
- Check site-specific parameter conflicts
- Verify location format (city, state)
- Test with simpler search terms
- Check if site is blocking requests

**2. High Duplicate Rates**
- Indicates narrow search criteria
- Consider expanding location/time windows
- Review search terms for specificity

**3. Scheduler Not Triggering**
- Verify Redis connectivity
- Check site schedule configuration
- Review scheduler daemon logs
- Confirm database permissions

**4. Jobs Not Persisting**
- Check database connectivity
- Verify jobs table schema
- Review worker logs for persistence errors
- Ensure required fields present (job_url, title, company)

### Debug Commands

**Check Scheduler Status**:
```python
from app.services.infrastructure.scheduler import get_scheduler_service
scheduler = get_scheduler_service()
await scheduler.initialize()
status = await scheduler.get_scheduler_status()
```

**Manual Scrape Test**:
```python
from app.services.jobspy.scraping import scrape_jobs_sync
result = scrape_jobs_sync({
    "site_name": "indeed",
    "search_term": "test",
    "location": "Remote",
    "results_wanted": 5
})
```

**Queue Inspection**:
```python
from app.services.infrastructure.queue import get_queue_service
queue = get_queue_service()
await queue.initialize()
info = queue.get_queue_info()
```

## Performance Considerations

### Resource Usage

**Memory**: ~50MB per worker process
**Network**: 1-5KB per job record
**Database**: ~2KB per job (including source_raw)
**Redis**: Minimal (locks + queue metadata)

### Scaling Guidelines

**Single Site**: 1 worker sufficient
**Multiple Sites**: 1 worker per 2-3 sites
**High Volume**: Consider dedicated workers per site

**Batch Size Recommendations**:
- Small deployments: 25-50 jobs per batch
- Medium deployments: 50-100 jobs per batch  
- Large deployments: 100-200 jobs per batch

## Future Enhancements

### Planned Improvements

1. **Advanced Location Parsing**: Extract city/state/country from job.location
2. **Cross-Site Deduplication**: Match identical jobs across different sites
3. **Salary Standardization**: Normalize compensation data
4. **Company Enrichment**: Add company metadata and URLs
5. **ML-Based Deduplication**: Semantic similarity matching

### API Extensions

1. **Real-time Pagination**: Stream results as they're scraped
2. **Custom Strategies**: User-defined pagination approaches  
3. **Site Health Monitoring**: Automatic site reliability tracking
4. **Adaptive Rate Limiting**: Dynamic pause adjustment based on response times

## Conclusion

The current JobSpy integration successfully overcomes the library's pagination limitations through intelligent workarounds while maintaining reliability and performance. The enhanced deduplication and comprehensive logging provide visibility into the scraping process and ensure data quality.

Key success factors:
- ✅ Pagination through time window splitting
- ✅ Robust deduplication at multiple levels  
- ✅ Comprehensive error handling and logging
- ✅ Site-specific parameter optimization
- ✅ Rate limiting and anti-detection measures

This implementation provides a solid foundation for reliable, large-scale job scraping while respecting site limitations and maintaining data integrity.