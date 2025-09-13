import asyncio
from domain.booking_experts.services import BookingExpertsClient
from uuid import uuid4
from app.shared.email_logger import send_execution_email
from config import get_settings
from venv import logger
from app.data.guesty_listings import guesty_listings
from typing import List, Any, Sequence
from app.domain.booking_experts.entities import SimplePrice, ComplexPrice

settings = get_settings()
BATCH_SIZE = 100
THROTTLE_SECONDS = 0.5

def _chunks(seq: Sequence[Any], size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]

class SyncCalendarPricesService:
    def __init__(self, booking_experts_client: BookingExpertsClient):
        self.booking_experts_client = booking_experts_client

    async def sync_prices(self, guesty_calendar: list = None, is_simple: bool = False) -> None:
        try:
            if not guesty_calendar:
                return
        
            sent = 0
            total = len(guesty_calendar)

            for batch in _chunks(guesty_calendar, BATCH_SIZE):
                simple_prices = []
                complex_prices = []

                for day in batch:
                    if day.listingId not in guesty_listings():
                        logger.info(f"Skipping listing {day.listingId} as it's in the skip list.")
                        continue
                    
                    if is_simple:
                        simple_prices.append(
                            SimplePrice(date=day.date, value=day.price, currency=day.currency).to_dict()
                        )
                    else:
                        complex_prices.append(
                            ComplexPrice(arrival_date=day.date, value=day.price, currency=day.currency).to_dict()
                        )

                await self.send_prices_to_api(simple_prices, complex_prices)
                sent += len(batch)

                 # Optional: tiny delay to avoid bursting right at the limit
                if THROTTLE_SECONDS:
                    await asyncio.sleep(THROTTLE_SECONDS)
        
            logger.info(f"Sent {sent}/{total} calendar items to Booking Experts in batches of {BATCH_SIZE}.")
            
        except Exception as e:
            send_execution_email(
                subject="Error Syncing Prices",
                body=f"An error occurred while syncing prices: {str(e)}. \n Guesty calendar: {str(guesty_calendar)}. \n Length: {len(guesty_calendar)}. \n Details: {str(simple_prices + complex_prices)}."
            )


    async def send_prices_to_api(self, simple_prices, complex_prices):
        if not simple_prices and not complex_prices:
            logger.info("No prices to sync.")
            return
        await self.booking_experts_client.patch_master_price_list(
                    price_list_id=settings.BOOKING_EXPERTS_MASTER_PRICE_LIST_ID,
                    administration_id=settings.BOOKING_EXPERTS_ADMINISTRATION_ID,
                    simple_prices=simple_prices,
                    complex_prices=complex_prices
                )
            