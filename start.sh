#!/bin/sh
set -euxo pipefail

# Initialize database schema
python - <<'PY'
import asyncio
from app.infrastructure.db.sqlite import init_db
asyncio.run(init_db())
print("DB schema ensured")
PY

# Run database migrations
echo "🔄 Running database migrations..."
python app/scripts/simple_migration.py

# Start the worker in the background
python -m app.workers.calendar_worker &

# Start the main application
exec uvicorn main:app --host 0.0.0.0 --port 8080
