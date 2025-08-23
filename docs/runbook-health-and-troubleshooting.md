## Health and Troubleshooting Runbook

### Health Endpoints
- `GET /health`: DB + Redis summary (`healthy`/`degraded`).
- `GET /health/detailed`: adds CPU/memory/disk via psutil.

Common statuses:
- DB unhealthy: verify `DATABASE_URL`, DB reachable, migrations run.
- Redis unhealthy: ensure Redis matches `REDIS_URL` or disable Redis-dependent checks.

### Logs
- Structured logs via `structlog` in JSON. Default to stdout.
- Uvicorn log level via `--log-level` or `.env DEBUG` for reload.

### Quick checks
```bash
curl -s http://localhost:8000/ | jq
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/health/detailed | jq
```

### Common Issues
- CORS blocked: ensure `BACKEND_CORS_ORIGINS` includes your frontend URL and is parsed as a list.
- 5xx on endpoints: check DB connectivity and that required tables exist.
- 404s from frontend API: confirm base URL in `frontend/src/services/api.ts` or `REACT_APP_API_URL`.

### Local services
```bash
# Postgres
psql "${DATABASE_URL}"

# Redis ping
redis-cli -u ${REDIS_URL} ping
```


