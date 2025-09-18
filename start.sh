#!/bin/sh
set -e

# Ensure schema exists before worker starts
python - <<'PY'
import asyncio
from app.db.sqlite import init_db
asyncio.run(init_db())
print("DB schema ensured")
PY

# Start the worker in the background
python -m app.workers.calendar_worker &

# Start the web app in the foreground
exec uvicorn main:app --host 0.0.0.0 --port 8080
