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
- **ChromaDB Integration**: Vector database support with configurable embedding services
- **Embedding Services**: Support for SentenceTransformer and OpenAI embeddings

## Quick Start

### Local Development

1. **Install Dependencies**:
   ```bash
   cd python-service
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Copy `.env.example` from the project root to `.env` and adjust the values as needed.

3. **Start Redis, Worker, and Scheduler**:
   ```bash
   redis-server
   python worker.py            # job worker
   python scheduler_daemon.py  # periodic scheduler
   ```

4. **Run the Service**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **View API Documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Development

Run with the full application stack:

```bash
# From the root directory
docker-compose up --build
```

The Python service will be available at http://localhost:8000

To run just the queue components:

```bash
docker-compose up redis worker scheduler
```

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
    ├── schemas/           # Pydantic schemas for requests and responses
    │   ├── __init__.py
    │   └── responses.py   # API response schemas
    └── services/          # Business logic services
        ├── __init__.py
        ├── gemini.py      # Gemini AI integration
        └── postgrest.py   # PostgREST API client
```

## Embedding Services

The service supports configurable embedding services for ChromaDB integration:

- **SentenceTransformer**: Local embedding models (default: BAAI/bge-m3)
- **OpenAI**: Cloud-based embeddings (text-embedding-3-small, text-embedding-3-large)

See [docs/EMBEDDING_CONFIGURATION.md](docs/EMBEDDING_CONFIGURATION.md) for detailed configuration instructions.

## Configuration

The service uses environment variables for configuration:

- `ENVIRONMENT`: Development/production mode
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `DEBUG`: Enable debug mode (true/false)
- `GEMINI_API_KEY`: Google Gemini AI API key
- `OPENAI_API_KEY`: OpenAI API key
- `HUGGING_FACE_API_KEY`: Hugging Face API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `POSTGREST_URL`: PostgREST backend URL
- `EMBEDDING_PROVIDER`: Embedding service provider (sentence_transformer, openai)
- `EMBEDDING_MODEL`: Model name for the embedding provider

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

