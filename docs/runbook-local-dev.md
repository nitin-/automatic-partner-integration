## Local Development Runbook

### Prerequisites
- Python 3.9+ (project venv included at `backend/venv`)
- Node.js 16+ and npm
- Docker (optional for Postgres/Redis)

### Environment
- Backend env file: `backend/.env`
- Key values to verify:
  - `DATABASE_URL` (ensure host/port exist; sample uses 5434)
  - `REDIS_URL` (optional for basic use; health checks will be degraded if not running)
  - `BACKEND_CORS_ORIGINS` (JSON array)
  - `DEBUG=false` for non-dev

### Start dependencies (recommended)
From repo root:

```bash
docker compose up -d db redis
```

If you don’t have compose services, run your own Postgres and Redis matching `.env`.

### Backend
```bash
cd backend
# Install (venv already present; update deps just in case)
./venv/bin/pip install -r requirements.txt

# Create/upgrade schema (optional if using create_all() on startup)
./venv/bin/alembic upgrade head

# Run API
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify:
```bash
curl -s http://localhost:8000/ | jq
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/health/detailed | jq   # requires Redis
```

### Frontend
```bash
cd frontend
npm ci
# Optional: set REACT_APP_API_URL, else defaults to http://localhost:8000
REACT_APP_API_URL=http://localhost:8000 npm start
```

Open `http://localhost:3000`.

### Lint/build
```bash
# Backend import smoke-check
cd backend && ../backend/venv/bin/python -c "import sys; sys.path.append('backend'); import app.main"

# Frontend build
cd frontend && npm run build
```


