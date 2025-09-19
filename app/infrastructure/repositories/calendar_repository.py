from __future__ import annotations
from typing import Iterable, List, Optional, Sequence, Tuple
from app.infrastructure.db.sqlite import open_db
from datetime import datetime

class CalendarRepository:
    """
    Async SQLite repository for Guesty calendar items.
    """

    async def upsert_days(self, days: Iterable, is_simple: bool) -> int:
        """
        Insert/replace days into the queue. Returns count written.
        'days' are objects with attributes: listingId, date, currency, price, status (optional).
        """
        to_insert: List[Tuple[str, str, str, float, Optional[str], int, int]] = []
        for d in days:
            to_insert.append((
                getattr(d, "listingId"),
                getattr(d, "date"),
                getattr(d, "currency"),
                float(getattr(d, "price")),
                getattr(d, "status", None),
                1 if is_simple else 0,
                0,  # processed
            ))

        if not to_insert:
            return 0

        sql = """
        INSERT INTO guesty_calendar_day (listing_id, date, currency, price, status, is_simple, processed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(listing_id, date, is_simple) DO UPDATE SET
          currency=excluded.currency,
          price=excluded.price,
          status=excluded.status,
          processed=0,
          created_at=datetime('now')
        """
        conn = await open_db()
        try:
            await conn.executemany(sql, to_insert)
            await conn.commit()
            return len(to_insert)
        finally:
            await conn.close()

    async def reserve_batch(self, limit: int, is_simple: Optional[bool] = None) -> List[dict]:
        """
        Reserve a batch (mark locked_at) and return rows as dicts.
        Uses a transaction to minimize double-reservations.
        """
        where_flag = "AND is_simple = ?" if is_simple is not None else ""
        params = [limit] if is_simple is None else [is_simple and 1 or 0, limit]

        conn = await open_db()
        try:
            await conn.execute("BEGIN IMMEDIATE;")

            # 1) Pick ids
            pick_sql = f"""
            SELECT id FROM guesty_calendar_day
            WHERE processed = 0 AND locked_at IS NULL {where_flag}
            ORDER BY created_at
            LIMIT ?
            """
            if is_simple is None:
                rows = await (await conn.execute(pick_sql, params)).fetchall()
            else:
                rows = await (await conn.execute(pick_sql, [1 if is_simple else 0, limit])).fetchall()

            if not rows:
                await conn.commit()
                return []

            ids = [r["id"] for r in rows]
            ids_tuple = "(" + ",".join("?" * len(ids)) + ")"

            # 2) Lock them
            now_iso = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            lock_sql = f"UPDATE guesty_calendar_day SET locked_at=? WHERE id IN {ids_tuple}"
            await conn.execute(lock_sql, [now_iso, *ids])
            await conn.commit()

            # 3) Fetch locked rows
            fetch_sql = f"SELECT * FROM guesty_calendar_day WHERE id IN {ids_tuple}"
            fetched = await (await conn.execute(fetch_sql, ids)).fetchall()
            return [dict(r) for r in fetched]
        finally:
            await conn.close()

    async def mark_processed(self, ids: Sequence[int]) -> None:
        if not ids:
            return
        conn = await open_db()
        try:
            ids_tuple = "(" + ",".join("?" * len(ids)) + ")"
            sql = f"UPDATE guesty_calendar_day SET processed=1, locked_at=NULL WHERE id IN {ids_tuple}"
            await conn.execute(sql, list(ids))
            await conn.commit()
        finally:
            await conn.close()

    async def release_locks(self, ids: Sequence[int]) -> None:
        """Unlock rows after a failure so they can be retried."""
        if not ids:
            return
        conn = await open_db()
        try:
            ids_tuple = "(" + ",".join("?" * len(ids)) + ")"
            sql = f"UPDATE guesty_calendar_day SET locked_at=NULL WHERE id IN {ids_tuple}"
            await conn.execute(sql, list(ids))
            await conn.commit()
        finally:
            await conn.close()

    async def count_unprocessed(self, is_simple: Optional[bool] = None) -> int:
        where_flag = "WHERE processed = 0" + ("" if is_simple is None else " AND is_simple = ?")
        conn = await open_db()
        try:
            if is_simple is None:
                row = await (await conn.execute(f"SELECT COUNT(*) c FROM guesty_calendar_day {where_flag}")).fetchone()
            else:
                row = await (await conn.execute(f"SELECT COUNT(*) c FROM guesty_calendar_day {where_flag}", [1 if is_simple else 0])).fetchone()
            return int(row["c"])
        finally:
            await conn.close()

    async def get_pending_prices_summary(self) -> List[dict]:
        """
        Get pending prices grouped by created_at date and hour.
        Returns list of dicts with date, hour, count, and is_simple.
        """
        conn = await open_db()
        try:
            sql = """
            SELECT 
                DATE(created_at) as date,
                CAST(STRFTIME('%H', created_at) AS INTEGER) as hour,
                is_simple,
                COUNT(*) as count
            FROM guesty_calendar_day 
            WHERE processed = 0
            GROUP BY DATE(created_at), STRFTIME('%H', created_at), is_simple
            ORDER BY date DESC, hour DESC, is_simple
            """
            rows = await (await conn.execute(sql)).fetchall()
            return [dict(r) for r in rows]
        finally:
            await conn.close()