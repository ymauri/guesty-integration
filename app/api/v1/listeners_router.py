from api.v1.schemas.guesty_schema import ListingCalendarUpdatedResponse
from fastapi import APIRouter
from application.sync_calendar_prices_service import SyncCalendarPricesService
from infrastructure.booking_experts.booking_experts_client import APIBookingExpertsClient
from application.retrieve_calendar_prices import RetrieveCalendarPrices
from infrastructure.guesty.guesty_client import GuestyClient
from fastapi import Depends
from app.shared.dependencies import get_sync_calendar_prices_service, get_retrieve_calendar_prices

router = APIRouter()

@router.post("/listing-calendar-update")
async def update_calendar_data(
    data: ListingCalendarUpdatedResponse,
    service: SyncCalendarPricesService = Depends(get_sync_calendar_prices_service),
):
    await service.sync_prices(data.calendar)
    return {"status": "Calendar updated"}  # explicit return helps tests

@router.get("/retrieve-calendar-prices")
async def retrieve_calendar_prices(
    listing_id: str,
    start_date: str,
    end_date: str,
    retriever: RetrieveCalendarPrices = Depends(get_retrieve_calendar_prices),
):
    return await retriever.get_calendar_prices(listing_id, start_date, end_date)
