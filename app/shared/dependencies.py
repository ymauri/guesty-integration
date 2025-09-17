from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from config import get_settings
from infrastructure.booking_experts.booking_experts_client import APIBookingExpertsClient
from infrastructure.guesty.guesty_client import GuestyClient
from application.sync_calendar_prices_service import SyncCalendarPricesService
from app.shared.cache import get_cache
from application.retrieve_calendar_prices import RetrieveCalendarPrices

settings = get_settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
    
def get_booking_experts_client() -> APIBookingExpertsClient:
    return APIBookingExpertsClient()

def get_guesty_client(cache = Depends(get_cache)) -> GuestyClient:
    return GuestyClient(cache)

def get_sync_calendar_prices_service(
    be_client: APIBookingExpertsClient = Depends(get_booking_experts_client),
) -> SyncCalendarPricesService:
    return SyncCalendarPricesService(be_client)

def get_retrieve_calendar_prices(
    guesty: GuestyClient = Depends(get_guesty_client),
    sync_service: SyncCalendarPricesService = Depends(get_sync_calendar_prices_service),
) -> RetrieveCalendarPrices:
    return RetrieveCalendarPrices(guesty, sync_service)