# Trainium Python AI Service

FastAPI-based microservice that provides AI capabilities for the Trainium Job Center application.

## Features

- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **Health Monitoring**: Built-in health check endpoints for system monitoring
- **Structured Logging**: Comprehensive logging with Loguru
- **Modular Architecture**: Organized code structure for easy maintenance and extension
- **Error Handling**: Standardized error responses across all endpoints
- **Async Support**: Built for high-performance asynchronous operations
- **Docker Ready**: Fully containerized for easy deployment
- **AI Integration Ready**: Prepared for Gemini AI integration

## Quick Start

### Local Development

1. **Install Dependencies**:
   ```bash
   cd python-service
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Copy `.env.example` from the project root to `.env` and adjust the values as needed.

3. **Run the Service**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **View API Documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Development

Run with the full application stack:

```bash
# From the root directory
docker-compose up --build
```

The Python service will be available at http://localhost:8000

## API Endpoints

### Health Checks

- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system information

### Root

- `GET /` - Service information and available endpoints

## Project Structure

```
python-service/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── app/
    ├── api/               # API endpoints
    │   ├── __init__.py
    │   └── health.py      # Health check endpoints
    ├── core/              # Core configuration
    │   ├── __init__.py
    │   └── config.py      # Application settings
    ├── models/            # Data models
    │   ├── __init__.py
    │   └── responses.py   # API response models
    └── services/          # Business logic services
        ├── __init__.py
        ├── gemini.py      # Gemini AI integration
        └── postgrest.py   # PostgREST API client
```

## Configuration

The service uses environment variables for configuration:

- `ENVIRONMENT`: Development/production mode
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `DEBUG`: Enable debug mode (true/false)
- `GEMINI_API_KEY`: Google Gemini AI API key
- `POSTGREST_URL`: PostgREST backend URL

## Future Enhancements

This service is designed to be extended with:

- Full Gemini AI integration for job application assistance
- Advanced job matching algorithms
- Resume analysis and optimization
- Interview preparation tools
- Asynchronous task processing with Celery
- Additional AI models and services

## Health Monitoring

The service includes comprehensive health checks:

- Service status and version information
- Dependency status (PostgREST, Gemini AI)
- Configuration validation
- System capabilities overview

Access health information at `/health` and `/health/detailed` endpoints.
## Development Checks

Run a basic syntax check before committing:

```bash
python -m py_compile $(git ls-files '*.py')
```

