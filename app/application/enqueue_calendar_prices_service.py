from domain.booking_experts.services import BookingExpertsClient
from app.shared.email_logger import send_execution_email
from config import get_settings
from venv import logger
from app.data.guesty_listings import guesty_listings
from app.infrastructure.repositories.calendar_repository import CalendarRepository

settings = get_settings()

class EnqueueCalendarPricesService:
    def __init__(self, booking_experts_client: BookingExpertsClient, repository: CalendarRepository):
        self.booking_experts_client = booking_experts_client
        self.repository = repository

    async def enqueue(self, guesty_calendar: list = None, is_simple: bool = False) -> None:
        """
        1) Save all days to SQLite (queue).
        Nothing stays loaded in memory beyond each small step.
        """
        if not guesty_calendar:
            return

        try:
            # Filter out listings you don't want to send at all
            filtered = [d for d in guesty_calendar if d.listingId in guesty_listings()]
            skipped = len(guesty_calendar) - len(filtered)
            if skipped:
                logger.info(f"Skipped {skipped} day(s) due to skip list.")

            # 1) Enqueue (upsert into DB)
            written = await self.repository.upsert_days(filtered, is_simple=is_simple)
            logger.info(f"Queued {written} day(s) into SQLite.")

        except Exception as e:
            self._email_error("Error Syncing Prices (enqueue/process)", e, guesty_calendar)
    
    def _email_error(self, subject: str, err: Exception, guesty_calendar=None, details=None):
        try:
            send_execution_email(
                subject=subject,
                body=(
                    f"Error: {str(err)}\n"
                    f"Guesty calendar (truncated): {str(guesty_calendar)[:1500] if guesty_calendar else '-'}\n"
                    f"Details: {str(details)[:1500] if details else '-'}"
                )
            )
        except Exception:
            pass