from domain.booking_experts.services import BookingExpertsClient
from uuid import uuid4

class SyncCalendarPricesService:
    def __init__(self, booking_experts_client: BookingExpertsClient):
        self.booking_experts_client = booking_experts_client

    async def sync_prices(self, price_list_id: str, administration_id: str, guesty_calendar: list = None) -> None:
        simple_prices = []
        for calendar_entry in guesty_calendar:
            simple_prices.append({
                "temp_id": uuid4().hex,
                "date": calendar_entry.date,
                "currency": calendar_entry.currency,
                "value": calendar_entry.price
            })

        await self.booking_experts_client.patch_master_price_list(
            price_list_id=price_list_id,
            administration_id=administration_id,
            simple_prices=simple_prices
        )

