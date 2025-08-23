## Database Migrations Runbook

### Setup Alembic
Alembic is configured in `backend/alembic.ini` and `backend/alembic/`.

### Create Migration
```bash
cd backend
./venv/bin/alembic revision -m "describe change"
```

Edit the generated script to include model changes if autogenerate isn’t used.

### Autogenerate (optional)
If you wire `target_metadata` to SQLAlchemy Base metadata, you can autogenerate:
```bash
./venv/bin/alembic revision --autogenerate -m "sync models"
```

### Apply Migrations
```bash
./venv/bin/alembic upgrade head
```

### Downgrade
```bash
./venv/bin/alembic downgrade -1
```


