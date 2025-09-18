from venv import logger
from typing import Any
from app.application.enqueue_calendar_prices_service import EnqueueCalendarPricesService
from app.infrastructure.guesty.guesty_client import GuestyClient
from app.application.enqueue_calendar_prices_service import EnqueueCalendarPricesService
from app.api.v1.schemas.guesty_schema import Day
from app.data.guesty_listings import guesty_listings

class RetrieveCalendarPrices:
    def __init__(self, guesty_client: GuestyClient, enqueue_calendar_prices_service: EnqueueCalendarPricesService):
        self.guesty_client = guesty_client
        self.enqueue_calendar_prices_service = enqueue_calendar_prices_service

    async def get_calendar_prices(self, listing_id: str, start_date: str, end_date: str, is_simple: bool = False) -> Any:
        try:
            if listing_id not in guesty_listings():
                logger.info(f"Skipping listing {listing_id} as it's in the skip list.")
                return {"status": "Listing skipped"}
            
            guesty_calendar = await self.guesty_client.list_calendar(listing_id, start_date, end_date)
            days = list(
                map(
                    lambda day: Day(**day), 
                    guesty_calendar["data"]["days"] if "data" in guesty_calendar and "days" in guesty_calendar["data"] else []
                )
            )
            await self.enqueue_calendar_prices_service.enqueue(days, is_simple)
            return {"status": "Calendar prices retrieved and sync initiated"}
        except Exception as e:
            logger.error(f"Error fetching calendar prices: {e}")
            raise e
