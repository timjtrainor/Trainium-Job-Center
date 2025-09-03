# Trainium Job Center

A full-stack job search assistant that helps manage applications, tailor resumes, track engagement, and support interviews.

## Project Structure

- **Front-end**: React + TypeScript app served with Vite.
- **python-service**: FastAPI microservice for AI-assisted features.
- **DB Scripts**: Database helpers and migrations.

## Prerequisites

- Node.js 18+
- Python 3.10+

## Run Front-end

```bash
npm install
npm run dev
```

Copy `.env.example` to `.env` and update the values (like `GEMINI_API_KEY` and database credentials) before starting.

## Run python-service

```bash
cd python-service
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service reads configuration from the `.env` file. API docs are available at `http://localhost:8000/docs`.

### Redis, Worker, and Scheduler

The queue system relies on a running Redis instance plus background worker and scheduler processes.

**Manual start:**

```bash
# Start Redis
redis-server

# In another terminal
cd python-service
python worker.py        # start job worker
python scheduler_daemon.py  # start scheduler
```

**Docker:**

```bash
docker-compose up redis worker scheduler
```

## Docker Compose

Run the full stack with Docker:

```bash
docker-compose up --build
```

## LLM Configuration for CrewAI personas

The service now supports multiple LLM providers with automatic fallback:

1. **Configure provider preferences** – Set `LLM_PREFERENCE` in `.env`:

   ```bash
   LLM_PREFERENCE=ollama:gemma3:1b,openai:gpt-4o-mini,gemini:gemini-1.5-flash
   ```

2. **Provider setup**:
   - **Ollama (default)**: Runs locally in Docker, no API key needed
   - **OpenAI**: Set `OPENAI_API_KEY` in `.env`
   - **Gemini**: Set `GEMINI_API_KEY` in `.env`
   - **Web search**: Set `TAVILY_API_KEY` for agent web search capabilities

3. **Model availability** – The Docker setup includes Ollama service with automatic gemma3:1b model pulling:

   ```bash
   docker-compose up --build
   ```

4. **Verify providers** – Check `/health` endpoint to see which providers are available.

The system automatically falls back to the next provider if the primary one fails, ensuring reliable operation.

## Checks

Run these commands before committing:

```bash
npm run build
python -m py_compile $(git ls-files '*.py')
```

See `AGENTS.md` for development conventions.
