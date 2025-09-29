# JobSpy Integration

The Trainium Job Center now includes JobSpy integration for automated job scraping from major job boards.

## Features

- **Multi-site scraping**: Support for Indeed, LinkedIn, Glassdoor, ZipRecruiter, and Google Jobs
- **Flexible search**: Search by keywords, location, job type, and remote work options
- **Async processing**: Non-blocking job scraping operations
- **Structured data**: Consistent job data format with company, title, location, salary, and description
- **Health monitoring**: Built-in health checks and service status monitoring

## API Endpoints

### POST `/jobs/scrape`
Scrape jobs from a specified job board.

**Request Body:**
```json
{
  "site_name": "indeed",
  "search_term": "python developer",
  "location": "remote",
  "is_remote": true,
  "results_wanted": 10
}
```

### GET `/jobs/sites`
Get information about supported job sites, including required filters and any conflicting criteria.

### GET `/jobs/sites/names`
List the identifiers of supported job sites.

### GET `/jobs/sites/names`
List the identifiers of supported job sites.

### GET `/jobs/health`
Check JobSpy service health status.

## Seattle Metro Job Search Examples

The following examples show optimal configurations for finding Product Manager roles in the Seattle metropolitan area (centered in Puyallup, WA/Seattle metro). Each site has different strengths for fresh vs. comprehensive results.

### Remote-Focused Product Manager Searches

#### Indeed (Best for Volume & Remote Jobs)
```bash
curl -X POST "http://localhost:8000/api/job-feed/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "indeed",
    "search_term": "product manager",
    "is_remote": true,
    "hours_old": 48,
    "results_wanted": 100,
    "country_indeed": "USA"
  }'
```

#### LinkedIn (Best for Fresh Tech Jobs)
```bash
curl -X POST "http://localhost:8000/api/job-feed/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "linkedin",
    "search_term": "product manager",
    "is_remote": true,
    "hours_old": 24,
    "results_wanted": 50,
    "linkedin_fetch_description": true
  }'
```

#### Google Jobs (Best for Local Remote Integration)
```bash
curl -X POST "http://localhost:8000/api/job-feed/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "google",
    "google_search_term": "product manager remote",
    "results_wanted": 50
  }'
```

#### ZipRecruiter (Backup Option)
```bash
curl -X POST "http://localhost:8000/api/job-feed/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "ziprecruiter",
    "search_term": "product manager",
    "is_remote": true,
    "hours_old": 48,
    "results_wanted": 50
  }'
```

#### Glassdoor (Best for Company Insights)
```bash
curl -X POST "http://localhost:8000/api/job-feed/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "glassdoor",
    "search_term": "product manager",
    "location": "remote",
    "hours_old": 72,
    "results_wanted": 30,
    "country_indeed": "USA"
  }'
```

### Location-Based Seattle Metro Searches

#### Indeed (Primary Choice for Seattle)
```bash
curl -X POST "http://localhost:8000/api/job-feed/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "indeed",
    "search_term": "product manager",
    "location": "Seattle, WA",
    "distance": 25,
    "hours_old": 72,
    "results_wanted": 100,
    "country_indeed": "USA"
  }'
```

#### LinkedIn (Strong for Tech Companies)
```bash
curl -X POST "http://localhost:8000/api/job-feed/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "linkedin",
    "search_term": "product manager",
    "location": "Seattle, WA",
    "distance": 25,
    "hours_old": 48,
    "results_wanted": 75,
    "linkedin_fetch_description": true
  }'
```

#### Google Jobs (Good Local Integration)
```bash
curl -X POST "http://localhost:8000/api/job-feed/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "google",
    "google_search_term": "product manager jobs Seattle WA",
    "results_wanted": 75
  }'
```

#### Glassdoor (Best Metro Reviews)
```bash
curl -X POST "http://localhost:8000/api/job-feed/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "glassdoor",
    "search_term": "product manager",
    "location": "Seattle, WA",
    "hours_old": 72,
    "results_wanted": 50,
    "country_indeed": "USA"
  }'
```

#### ZipRecruiter (Regional Focus)
```bash
curl -X POST "http://localhost:8000/api/job-feed/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "ziprecruiter",
    "search_term": "product manager",
    "location": "Seattle, WA",
    "distance": 25,
    "hours_old": 72,
    "results_wanted": 75
  }'
```

## Batch Scraping for Comprehensive Coverage

For maximum job discovery, run all sites simultaneously:

```bash
# Remote PM jobs
for site in indeed linkedin google ziprecruiter glassdoor; do
  echo "Starting $site..."
  curl -X POST "http://localhost:8000/api/job-feed/scrape" \
    -H "Content-Type: application/json" \
    -d "{\"site_name\":\"$site\",\"search_term\":\"product manager\",\"is_remote\":true,\"hours_old\":48,\"results_wanted\":100}" &
done
```

## Anti-Bot Protection Recommendations

To minimize bot blocking while maximizing fresh results:

- **Spider delays**: 2-5 seconds between requests (automatic)
- **IP rotation**: Use different network paths if available
- **Site limits**: Max 1 concurrent scrape per site
- **Time windows**: Rotate `hours_old` values (24h, 48h, 72h)
- **Location targeting**: Include regional searches (Seattle, Portland, etc.)

## Configuration Parameters

### Common Parameters
- `hours_old`: Focus on recent jobs (24-72h recommended)
- `results_wanted`: Request 50-100 for comprehensive coverage
- `is_remote`: Set `true` for distributed workforce roles
- `distance`: Use 25 miles for metro area searches

### Site-Specific Notes

#### Indeed & Glassdoor
- Require `country_indeed: "USA"`
- Prioritize `hours_old` over other filters
- Best for large job volumes

#### LinkedIn
- Use `linkedin_fetch_description: true` for full job details
- Most fresh tech and PM positions
- Support `linkedin_company_ids` for targeted companies

#### Google Jobs
- Requires `google_search_term` instead of separate fields
- Combine search terms: `"product manager remote Seattle"`

#### ZipRecruiter
- Moderate freshness, good backup option
- Supports all standard filters

## Dependencies

The integration adds `python-jobspy==1.1.82` to the requirements, which includes:
- Beautiful Soup for HTML parsing
- Pandas for data manipulation
- Requests for HTTP operations
- Additional scraping utilities

## Integration with Existing Features

The scraped job data is structured to work seamlessly with the existing Trainium Job Center workflow:
- Job descriptions are provided in markdown format (consistent with current app)
- Data can be easily integrated with the AI analysis pipeline
- Supports the existing application creation and tracking workflow
