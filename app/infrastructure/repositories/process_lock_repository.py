from typing import Optional
from datetime import datetime, timedelta
import aiosqlite
from app.infrastructure.db.sqlite import open_db

class ProcessLockRepository:
    async def acquire_worker_lock(self, name: str, ttl_seconds: int = 300) -> bool:
        """
        Try to acquire a named lock with a TTL. Returns True if acquired.
        Safe for SQLite because we rely on a simple upsert + time check.
        """
        conn = await open_db()
        try:
            await conn.execute("BEGIN IMMEDIATE;")
            row = await (await conn.execute(
                "SELECT acquired_at FROM process_lock WHERE name = ?", [name]
            )).fetchone()
            now = datetime.utcnow()
            if row:
                acquired_at = datetime.strptime(row["acquired_at"], "%Y-%m-%d %H:%M:%S")
                if now - acquired_at < timedelta(seconds=ttl_seconds):
                    await conn.commit()
                    return False
                # stale -> replace
                await conn.execute(
                    "UPDATE process_lock SET acquired_at = ? WHERE name = ?",
                    [now.strftime("%Y-%m-%d %H:%M:%S"), name]
                )
            else:
                await conn.execute(
                    "INSERT INTO process_lock (name, acquired_at) VALUES (?, ?)",
                    [name, now.strftime("%Y-%m-%d %H:%M:%S")]
                )
            await conn.commit()
            return True
        finally:
            await conn.close()

    async def refresh_worker_lock(self, name: str) -> None:
        conn = await open_db()
        try:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            await conn.execute("UPDATE process_lock SET acquired_at=? WHERE name=?", [now, name])
            await conn.commit()
        finally:
            await conn.close()

    async def release_worker_lock(self, name: str) -> None:
        conn = await open_db()
        try:
            await conn.execute("DELETE FROM process_lock WHERE name=?", [name])
            await conn.commit()
        finally:
            await conn.close()
