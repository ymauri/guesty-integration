from domain.booking_experts.services import BookingExpertsClient
from uuid import uuid4
from app.data.room_mapping_loader import load_room_mapping
from app.shared.email_logger import send_execution_email

class SyncCalendarPricesService:
    def __init__(self, booking_experts_client: BookingExpertsClient):
        self.booking_experts_client = booking_experts_client

    async def sync_prices(self, guesty_calendar: list = None) -> None:
        if not guesty_calendar:
            return
        
        room_mapping = load_room_mapping()
        calendar_entries_by_listing = {}
        
        for entry in guesty_calendar:
            calendar_entries_by_listing.setdefault(entry["listingId"], []).append(entry)

        for listing_id, calendar_entries in calendar_entries_by_listing.items():
            simple_prices = []
            for calendar_entry in calendar_entries:
                simple_prices.append({
                    "temp_id": uuid4().hex,
                    "date": calendar_entry["date"],
                    "currency": calendar_entry["currency"],
                    "value": calendar_entry["price"]
                })

            try:
                for mapping in room_mapping:
                    if mapping["guesty_listing_id"] == listing_id:
                        price_list_id = mapping["booking_experts_price_list_id"]
                        administration_id = mapping["booking_experts_administration_id"]

                        await self.booking_experts_client.patch_master_price_list(
                            price_list_id=price_list_id,
                            administration_id=administration_id,
                            simple_prices=simple_prices
                        )

                        send_execution_email(
                            subject="Prices Synced Successfully",
                            body=f"Prices for listing {mapping['name']} have been synced successfully. \n Details: {str(simple_prices)}"
                        )

                        break
            except Exception as e:
                send_execution_email(
                    subject="Error Syncing Prices",
                    body=f"An error occurred while syncing prices for listing {mapping['name']}: {str(e)}"
                )
                continue