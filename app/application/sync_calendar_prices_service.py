from domain.booking_experts.services import BookingExpertsClient
from uuid import uuid4
from app.shared.email_logger import send_execution_email
from config import get_settings
from venv import logger
from app.data.guesty_listings import guesty_listings

settings = get_settings()

class SyncCalendarPricesService:
    def __init__(self, booking_experts_client: BookingExpertsClient):
        self.booking_experts_client = booking_experts_client

    async def sync_prices(self, guesty_calendar: list = None, is_simple: bool = False) -> None:
        try:
            if not guesty_calendar:
                return
        
            simple_prices = []
            complex_prices = []
            for day in guesty_calendar:
                
                if day.listingId not in guesty_listings():
                    logger.info(f"Skipping listing {day.listingId} as it's in the skip list.")
                    continue
                
                if is_simple:
                    simple_prices.append({
                        "temp_id": uuid4().hex,
                        "date": day.date,
                        "currency": day.currency,
                        "value": day.price
                    })
                else:
                    complex_prices.append({
                        "temp_id": uuid4().hex,
                        "arrival_date": day.date,
                        "currency": day.currency,
                        "value": day.price,
                        "length_of_stay": 1
                    })
                    
            if not simple_prices and not complex_prices:
                logger.info("No prices to sync.")
                return

            await self.booking_experts_client.patch_master_price_list(
                price_list_id=settings.BOOKING_EXPERTS_MASTER_PRICE_LIST_ID,
                administration_id=settings.BOOKING_EXPERTS_ADMINISTRATION_ID,
                simple_prices=simple_prices,
                complex_prices=complex_prices
            )
            
        except Exception as e:
            send_execution_email(
                subject="Error Syncing Prices",
                body=f"An error occurred while syncing prices: {str(e)}. \n Guesty calendar: {str(guesty_calendar)}. \n Details: {str(simple_prices + complex_prices)}"
            )
            