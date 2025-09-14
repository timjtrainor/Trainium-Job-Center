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

## Usage Example

```bash
# Scrape Python developer jobs from Indeed
curl -X POST "http://localhost:8000/jobs/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "indeed",
    "search_term": "python developer",
    "location": "remote",
    "is_remote": true,
    "results_wanted": 5
  }'
```

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