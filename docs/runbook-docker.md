## Docker Runbook

### Build Images
```bash
docker build -t lender-backend:latest backend
docker build -t lender-frontend:latest frontend
```

### Run Backend
```bash
docker run --rm -p 8000:8000 \
  --env-file backend/.env \
  -v $(pwd)/backend/uploads:/app/uploads \
  -v $(pwd)/backend/generated_apis:/app/generated_apis \
  lender-backend:latest
```

Note: Healthcheck is at `/health`.

### Run Frontend
```bash
docker run --rm -p 3000:80 \
  -e REACT_APP_API_URL=http://host.docker.internal:8000 \
  lender-frontend:latest
```

### Compose (example)
Define services for Postgres/Redis and both apps, then:
```bash
docker compose up -d
```


