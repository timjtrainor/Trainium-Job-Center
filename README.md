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

## Use Llama-4 for CrewAI personas

1. **Update persona definitions** – In `python-service/app/services/persona_catalog.yaml` set each persona to the Hugging Face model:

   ```yaml
   models:
     - provider: huggingface
       model: meta-llama/Llama-4
   ```

2. **Use the Hugging Face client** – `python-service/app/services/llm_clients.py` already includes a minimal `HuggingFaceClient`. Extend it if custom behavior is needed and ensure it's registered in `_CLIENT_FACTORIES`.

3. **Expose credentials** – Set `HUGGING_FACE_API_KEY` in `.env`; this key is forwarded to containers by `docker-compose.yml`.

4. **Make the model available** – The `python-service/Dockerfile` installs Hugging Face dependencies and downloads the `meta-llama/Llama-4` weights during the image build. Rebuild to apply:

   ```bash
   docker-compose up --build
   ```

With these steps, the python service will have Llama‑4 locally for CrewAI personas.

## Checks

Run these commands before committing:

```bash
npm run build
python -m py_compile $(git ls-files '*.py')
```

See `AGENTS.md` for development conventions.
