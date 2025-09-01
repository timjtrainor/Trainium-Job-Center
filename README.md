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

## Docker Compose

Run the full stack with Docker:

```bash
docker-compose up --build
```

## Checks

Run these commands before committing:

```bash
npm run build
python -m py_compile $(git ls-files '*.py')
```

See `AGENTS.md` for development conventions.
