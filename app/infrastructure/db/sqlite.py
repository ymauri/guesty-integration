# app/db/sqlite.py
import os
import aiosqlite
from pathlib import Path
from app.config import get_settings

settings = get_settings()

# Use /data on Fly.io (bind a Volume there). Falls back to local file.
DB_PATH = settings.SQLITE_DB_PATH

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS guesty_calendar_day (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  listing_id TEXT NOT NULL,
  date TEXT NOT NULL,              -- ISO yyyy-mm-dd
  currency TEXT NOT NULL,
  price REAL NOT NULL,
  status TEXT,
  is_simple INTEGER NOT NULL DEFAULT 0,  -- 0=complex,1=simple
  processed INTEGER NOT NULL DEFAULT 0,  -- 0=pending,1=done
  locked_at TEXT DEFAULT NULL,           -- ISO datetime when reserved by a worker
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(listing_id, date, is_simple) ON CONFLICT REPLACE
);

CREATE INDEX IF NOT EXISTS idx_gcd_processed ON guesty_calendar_day(processed, is_simple);
CREATE INDEX IF NOT EXISTS idx_gcd_locked ON guesty_calendar_day(locked_at);
CREATE INDEX IF NOT EXISTS idx_gcd_created ON guesty_calendar_day(created_at);

CREATE TABLE IF NOT EXISTS process_lock (
  name TEXT PRIMARY KEY,
  acquired_at TEXT NOT NULL
);
"""

async def ensure_db_dir():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

async def open_db():
    await ensure_db_dir()
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys=ON;")
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

async def init_db():
    conn = await open_db()
    try:
        await conn.executescript(SCHEMA)
        await conn.commit()
    finally:
        await conn.close()
    print("✅ SQLite database initialized.")