from domain.booking_experts.services import BookingExpertsClient
from uuid import uuid4
from app.shared.email_logger import send_execution_email
from config import get_settings

settings = get_settings()

class SyncCalendarPricesService:
    def __init__(self, booking_experts_client: BookingExpertsClient):
        self.booking_experts_client = booking_experts_client

    async def sync_prices(self, guesty_calendar: list = None) -> None:
        try:
            if not guesty_calendar:
                return
        
            simple_prices = []
            for day in guesty_calendar:
                simple_prices.append({
                    "temp_id": uuid4().hex,
                    "date": day["date"],
                    "currency": day["currency"],
                    "value": day["price"]
                })

            await self.booking_experts_client.patch_master_price_list(
                price_list_id=settings.BOOKING_EXPERTS_MASTER_PRICE_LIST_ID,
                administration_id=settings.BOOKING_EXPERTS_ADMINISTRATION_ID,
                simple_prices=simple_prices
            )
            
        except Exception as e:
            send_execution_email(
                subject="Error Syncing Prices",
                body=f"An error occurred while syncing prices: {str(e)}. \n Guesty calendar: {str(guesty_calendar)}. \n Details: {str(simple_prices)}"
            )
            