from api.v1.schemas.guesty_schema import ListingCalendarUpdatedResponse
from fastapi import APIRouter, Depends
from application.sync_calendar_prices_service import SyncCalendarPricesService
from infrastructure.booking_experts.booking_experts_client import APIBookingExpertsClient

router = APIRouter()
client = SyncCalendarPricesService(APIBookingExpertsClient())

@router.post("/listing-calendar-update")
async def update_calendar_data(data: ListingCalendarUpdatedResponse):

    # Call the appropriate method on the client to update the calendar data
    await client.sync_prices(1, 1, data.calendar)

