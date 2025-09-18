#!/bin/sh
set -euxo pipefail

python - <<'PY'
import asyncio
from app.infrastructure.db.sqlite import init_db
asyncio.run(init_db())
print("DB schema ensured")
PY

python -m app.workers.calendar_worker &
exec uvicorn main:app --host 0.0.0.0 --port 8080
