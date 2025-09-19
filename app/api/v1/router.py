from api.v1.schemas.guesty_schema import ListingCalendarUpdatedResponse, WorkerStatusSummary
from fastapi import APIRouter
from app.application.enqueue_calendar_prices_service import EnqueueCalendarPricesService
from application.retrieve_calendar_prices import RetrieveCalendarPrices
from fastapi import Depends
from app.shared.dependencies import get_enqueue_calendar_prices_service, get_retrieve_calendar_prices, get_worker_status_service
from app.application.worker_status_service import WorkerStatusService

router = APIRouter()

@router.post("/listing-calendar-update")
async def update_calendar_data(
    data: ListingCalendarUpdatedResponse,
    service: EnqueueCalendarPricesService = Depends(get_enqueue_calendar_prices_service),
):
    await service.enqueue(data.calendar)
    return {"status": "Calendar queued"}  # explicit return helps tests

@router.get("/retrieve-calendar-prices")
async def retrieve_calendar_prices(
    listing_id: str,
    start_date: str,
    end_date: str,
    is_simple: bool = False,
    retriever: RetrieveCalendarPrices = Depends(get_retrieve_calendar_prices),
):
    return await retriever.get_calendar_prices(listing_id, start_date, end_date, is_simple)

@router.get("/worker-status", response_model=WorkerStatusSummary)
async def get_worker_status(
    service: WorkerStatusService = Depends(get_worker_status_service),
):
    """
    Get a summary of worker status showing pending prices grouped by created_at date and hour.
    """
    return await service.get_worker_status_summary()
