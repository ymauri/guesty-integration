from __future__ import annotations
from typing import List, Optional, Dict
from app.infrastructure.db.sqlite import open_db


class ListingPriceListRepository:
    """
    Repository for managing Guesty listing to Booking Experts price list mappings.
    """

    async def create_mapping(
        self, 
        guesty_listing_id: str, 
        booking_experts_price_list_id: str
    ) -> int:
        """
        Create a new listing to price list mapping.
        Returns the ID of the created mapping.
        """
        conn = await open_db()
        try:
            sql = """
            INSERT INTO listing_price_list_mapping 
            (guesty_listing_id, booking_experts_price_list_id, is_active)
            VALUES (?, ?, 1)
            """
            cursor = await conn.execute(sql, [guesty_listing_id, booking_experts_price_list_id])
            await conn.commit()
            return cursor.lastrowid
        finally:
            await conn.close()

    async def get_mapping(self, guesty_listing_id: str) -> Optional[Dict]:
        """
        Get the price list mapping for a specific Guesty listing ID.
        Returns None if not found or inactive.
        """
        conn = await open_db()
        try:
            sql = """
            SELECT * FROM listing_price_list_mapping 
            WHERE guesty_listing_id = ? AND is_active = 1
            """
            row = await (await conn.execute(sql, [guesty_listing_id])).fetchone()
            return dict(row) if row else None
        finally:
            await conn.close()

    async def get_all_mappings(self, active_only: bool = True) -> List[Dict]:
        """
        Get all listing to price list mappings.
        """
        conn = await open_db()
        try:
            where_clause = "WHERE is_active = 1" if active_only else ""
            sql = f"SELECT * FROM listing_price_list_mapping {where_clause} ORDER BY created_at DESC"
            rows = await (await conn.execute(sql)).fetchall()
            return [dict(row) for row in rows]
        finally:
            await conn.close()

    async def update_mapping(
        self, 
        guesty_listing_id: str, 
        booking_experts_price_list_id: str
    ) -> bool:
        """
        Update the price list for a specific Guesty listing ID.
        Returns True if updated, False if not found.
        """
        conn = await open_db()
        try:
            sql = """
            UPDATE listing_price_list_mapping 
            SET booking_experts_price_list_id = ?, updated_at = datetime('now')
            WHERE guesty_listing_id = ? AND is_active = 1
            """
            cursor = await conn.execute(sql, [booking_experts_price_list_id, guesty_listing_id])
            await conn.commit()
            return cursor.rowcount > 0
        finally:
            await conn.close()

    async def deactivate_mapping(self, guesty_listing_id: str) -> bool:
        """
        Deactivate a listing to price list mapping.
        Returns True if deactivated, False if not found.
        """
        conn = await open_db()
        try:
            sql = """
            UPDATE listing_price_list_mapping 
            SET is_active = 0, updated_at = datetime('now')
            WHERE guesty_listing_id = ?
            """
            cursor = await conn.execute(sql, [guesty_listing_id])
            await conn.commit()
            return cursor.rowcount > 0
        finally:
            await conn.close()

    async def get_price_list_for_listing(self, guesty_listing_id: str) -> Optional[str]:
        """
        Get the Booking Experts price list ID for a Guesty listing.
        Returns None if not found or inactive.
        """
        mapping = await self.get_mapping(guesty_listing_id)
        return mapping["booking_experts_price_list_id"] if mapping else None

    async def get_listings_for_price_list(self, booking_experts_price_list_id: str) -> List[str]:
        """
        Get all Guesty listing IDs that are mapped to a specific price list.
        """
        conn = await open_db()
        try:
            sql = """
            SELECT guesty_listing_id FROM listing_price_list_mapping 
            WHERE booking_experts_price_list_id = ? AND is_active = 1
            """
            rows = await (await conn.execute(sql, [booking_experts_price_list_id])).fetchall()
            return [row["guesty_listing_id"] for row in rows]
        finally:
            await conn.close()

    async def bulk_create_mappings(self, mappings: List[Dict[str, str]]) -> int:
        """
        Create multiple mappings in a single transaction.
        mappings: List of dicts with 'guesty_listing_id' and 'booking_experts_price_list_id'
        Returns the number of mappings created.
        """
        if not mappings:
            return 0

        conn = await open_db()
        try:
            sql = """
            INSERT OR REPLACE INTO listing_price_list_mapping 
            (guesty_listing_id, booking_experts_price_list_id, is_active)
            VALUES (?, ?, 1)
            """
            data = [(m["guesty_listing_id"], m["booking_experts_price_list_id"]) for m in mappings]
            await conn.executemany(sql, data)
            await conn.commit()
            return len(data)
        finally:
            await conn.close()
