import asyncio
import random
from typing import Optional, Dict
from app.config import get_settings
from app.infrastructure.repositories.calendar_repository import CalendarRepository
from app.infrastructure.repositories.process_lock_repository import ProcessLockRepository
from app.infrastructure.repositories.listing_price_list_repository import ListingPriceListRepository
from app.infrastructure.booking_experts.booking_experts_client import BookingExpertsClient
from uuid import uuid4
from app.shared.email_logger import send_execution_email
from app.domain.exceptions.max_batch_errors_exceeded import MaxBatchErrorsExceeded

settings = get_settings()

class SyncCalendarPricesService:
    def __init__(
        self,
        repository: CalendarRepository,
        process_lock_repository: ProcessLockRepository,
        listing_price_list_repository: ListingPriceListRepository,
        booking_experts_client: BookingExpertsClient,
    ):
        self.repository = repository
        self.process_lock_repository = process_lock_repository
        self.listing_price_list_repository = listing_price_list_repository
        self.booking_experts_client = booking_experts_client

    async def drain_queue_tick(
        self,
        *,
        is_simple: bool,
        batch_size: int = 20,
        max_batches_this_tick: int = 5,
        inter_batch_sleep_ms: int = 250,
        max_errors_per_tick: int = 3
    ) -> int:
        """
        Process up to `max_batches_this_tick` batches, sleeping briefly between them.
        Returns the number of rows processed in this tick.
        """
        processed_rows = 0
        consecutive_errors = 0

        for _ in range(max_batches_this_tick):
            batch_rows = await self.repository.reserve_batch(limit=batch_size, is_simple=is_simple)
            if not batch_rows:
                break

            try:
                # Group prices by their respective price lists
                price_lists_data = await self._group_prices_by_price_list(batch_rows, is_simple)
                
                # Process each price list separately
                for price_list_id, price_data in price_lists_data.items():
                    await self.booking_experts_client.patch_master_price_list(
                        price_list_id=price_list_id,
                        administration_id=settings.BOOKING_EXPERTS_ADMINISTRATION_ID,
                        simple_prices=price_data["simple_prices"],
                        complex_prices=price_data["complex_prices"]
                    )
                
                await self.repository.mark_processed([r["id"] for r in batch_rows])
                processed_rows += len(batch_rows)

                consecutive_errors = 0

                # Rate limiting: tiny pause + jitter to avoid thundering herd / API timeout
                sleep_ms = inter_batch_sleep_ms + random.randint(0, 200)
                await asyncio.sleep(sleep_ms / 1000.0)

            except Exception as be_err:
                await self.repository.release_locks([r["id"] for r in batch_rows])
                self._email_error("Error sending batch to Booking Experts", be_err, details=batch_rows)

                consecutive_errors += 1
                if consecutive_errors >= max_errors_per_tick:
                    # Stop this tick immediately
                    raise MaxBatchErrorsExceeded(
                        f"More than {max_errors_per_tick} errors occurred in this tick."
                    )
                # Backoff before trying the next batch
                await asyncio.sleep(1.0 + random.random())
                # continue to next batch
        return processed_rows

    async def _group_prices_by_price_list(self, rows: list[dict], is_simple: bool) -> Dict[str, Dict]:
        """
        Group prices by their respective Booking Experts price list IDs.
        Returns a dictionary where keys are price_list_ids and values contain simple_prices and complex_prices.
        """
        price_lists_data = {}
        
        for row in rows:
            # Get the price list ID for this listing
            price_list_id = await self.listing_price_list_repository.get_price_list_for_listing(row["listing_id"])
            
            # Skip if no price list mapping found
            if not price_list_id:
                continue
                
            if price_list_id not in price_lists_data:
                price_lists_data[price_list_id] = {
                    "simple_prices": [],
                    "complex_prices": []
                }
            
            # Create price data based on type
            if is_simple:
                price_data = {
                    "temp_id": uuid4().hex,
                    "date": row["date"],
                    "currency": row["currency"],
                    "value": row["price"],
                }
                price_lists_data[price_list_id]["simple_prices"].append(price_data)
            else:
                price_data = {
                    "temp_id": uuid4().hex,
                    "arrival_date": row["date"],
                    "currency": row["currency"],
                    "value": row["price"],
                    "length_of_stay": 1,
                }
                price_lists_data[price_list_id]["complex_prices"].append(price_data)
        
        return price_lists_data

    def _map_rows_to_be_payload(self, rows: list[dict], is_simple: bool):
        """
        Legacy method - kept for backward compatibility but not used in the new flow.
        """
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
    
    def _email_error(self, subject: str, err: Exception, guesty_calendar=None, details=None):
        try:
            send_execution_email(
                subject=subject,
                body=(
                    f"Error: {str(err)}\n"
                    f"Guesty calendar (truncated): {str(guesty_calendar) if guesty_calendar else '-'}\n"
                    f"Details: {str(details) if details else '-'}"
                )
            )
        except Exception:
            pass