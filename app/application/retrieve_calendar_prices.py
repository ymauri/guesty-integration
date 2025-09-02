from venv import logger
from typing import Any
from app.application.sync_calendar_prices_service import SyncCalendarPricesService
from app.infrastructure.guesty.guesty_client import GuestyClient
from app.application.sync_calendar_prices_service import SyncCalendarPricesService

class RetrieveCalendarPrices:
    def __init__(self, guesty_client: GuestyClient, sync_calendar_prices_service: SyncCalendarPricesService):
        self.guesty_client = guesty_client
        self.sync_calendar_prices_service = sync_calendar_prices_service

    async def get_calendar_prices(self, listing_id: str, start_date: str, end_date: str) -> Any:
        try:
            guesty_calendar = await self.guesty_client.list_calendar(listing_id, start_date, end_date)
            await self.sync_calendar_prices_service.sync_prices(guesty_calendar.data.days if guesty_calendar and "data" in guesty_calendar and "days" in guesty_calendar["data"] else [])
            return {"status": "Calendar prices retrieved and sync initiated"}
        except Exception as e:
            logger.error(f"Error fetching calendar prices: {e}")
            raise e
