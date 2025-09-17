from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from config import get_settings
from app.infrastructure.booking_experts.booking_experts_client import APIBookingExpertsClient
from app.infrastructure.guesty.guesty_client import GuestyClient
from app.application.enqueue_calendar_prices_service import EnqueueCalendarPricesService
from app.shared.cache import get_cache
from app.application.retrieve_calendar_prices import RetrieveCalendarPrices
from app.infrastructure.repositories.calendar_repository import CalendarRepository
from app.infrastructure.repositories.process_lock_repository import ProcessLockRepository
from app.application.sync_calendar_prices_service import SyncCalendarPricesService

settings = get_settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
    
def get_booking_experts_client() -> APIBookingExpertsClient:
    return APIBookingExpertsClient()

def get_guesty_client(cache = Depends(get_cache)) -> GuestyClient:
    return GuestyClient(cache)

def get_calendar_repository() -> CalendarRepository:
    return CalendarRepository()

def get_process_lock_repository() -> ProcessLockRepository:
    return ProcessLockRepository()

def get_enqueue_calendar_prices_service(
    be_client: APIBookingExpertsClient = Depends(get_booking_experts_client),
    repository: CalendarRepository = Depends(get_calendar_repository),
) -> EnqueueCalendarPricesService:
    return EnqueueCalendarPricesService(be_client, repository)

def get_sync_calendar_prices_service(
    repository: CalendarRepository = Depends(get_calendar_repository),
    process_lock_repository: ProcessLockRepository = Depends(get_process_lock_repository),
    be_client: APIBookingExpertsClient = Depends(get_booking_experts_client),
    email_errors_to: Annotated[str | None, Depends(lambda: settings.EMAIL_ERRORS_TO)] = None,
) -> SyncCalendarPricesService:
    from app.application.sync_calendar_prices_service import SyncCalendarPricesService
    return SyncCalendarPricesService(repository, process_lock_repository, be_client, email_errors_to)

def get_retrieve_calendar_prices(
    guesty: GuestyClient = Depends(get_guesty_client),
    sync_service: EnqueueCalendarPricesService = Depends(get_enqueue_calendar_prices_service),
) -> RetrieveCalendarPrices:
    return RetrieveCalendarPrices(guesty, sync_service)