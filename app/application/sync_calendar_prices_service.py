import asyncio
import random
from typing import Optional
from config import get_settings
from app.infrastructure.repositories.calendar_repository import CalendarRepository
from app.infrastructure.repositories.process_lock_repository import ProcessLockRepository
from app.infrastructure.booking_experts.booking_experts_client import BookingExpertsClient
from uuid import uuid4

settings = get_settings()

class SyncCalendarPricesService:
    def __init__(
        self,
        repository: CalendarRepository,
        process_lock_repository: ProcessLockRepository,
        booking_experts_client: BookingExpertsClient,
        email_errors_to: Optional[str] = None
    ):
        self.repository = repository
        self.process_lock_repository = process_lock_repository
        self.booking_experts_client = booking_experts_client
        self.email_errors_to = email_errors_to

    async def drain_queue_tick(
        self,
        *,
        is_simple: bool,
        batch_size: int = 20,
        max_batches_this_tick: int = 5,
        inter_batch_sleep_ms: int = 250
    ) -> int:
        """
        Process up to `max_batches_this_tick` batches, sleeping briefly between them.
        Returns the number of rows processed in this tick.
        """
        processed_rows = 0
        for _ in range(max_batches_this_tick):
            batch_rows = await self.repository.reserve_batch(limit=batch_size, is_simple=is_simple)
            if not batch_rows:
                break

            try:
                simple_prices, complex_prices = self._map_rows_to_be_payload(batch_rows, is_simple)
                await self.booking_experts_client.patch_master_price_list(
                    price_list_id=settings.BOOKING_EXPERTS_MASTER_PRICE_LIST_ID,
                    administration_id=settings.BOOKING_EXPERTS_ADMINISTRATION_ID,
                    simple_prices=simple_prices,
                    complex_prices=complex_prices
                )
                await self.repository.mark_processed([r["id"] for r in batch_rows])
                processed_rows += len(batch_rows)

                # Rate limiting: tiny pause + jitter to avoid thundering herd / API timeout
                sleep_ms = inter_batch_sleep_ms + random.randint(0, 200)
                await asyncio.sleep(sleep_ms / 1000.0)

            except Exception as be_err:
                await self.repository.release_locks([r["id"] for r in batch_rows])
                self._email_error("Error sending batch to Booking Experts", be_err, details=batch_rows)
                # Backoff before trying the next batch
                await asyncio.sleep(1.0 + random.random())
                # continue to next batch
        return processed_rows

    def _map_rows_to_be_payload(self, rows: list[dict], is_simple: bool):
        if is_simple:
            simple_prices = [{
                "temp_id": uuid4().hex,
                "date": r["date"],
                "currency": r["currency"],
                "value": r["price"],
            } for r in rows]
            return simple_prices, []
        else:
            complex_prices = [{
                "temp_id": uuid4().hex,
                "arrival_date": r["date"],
                "currency": r["currency"],
                "value": r["price"],
                "length_of_stay": 1,
            } for r in rows]
            return [], complex_prices