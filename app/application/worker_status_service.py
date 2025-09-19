from typing import List
from app.infrastructure.repositories.calendar_repository import CalendarRepository
from app.api.v1.schemas.guesty_schema import WorkerStatusSummary, PendingPriceSummary


class WorkerStatusService:
    """
    Service for managing worker status and pending prices summary.
    """
    
    def __init__(self, repository: CalendarRepository):
        self.repository = repository
    
    async def get_worker_status_summary(self) -> WorkerStatusSummary:
        """
        Get a summary of worker status showing pending prices grouped by created_at date and hour.
        
        Returns:
            WorkerStatusSummary: Contains total pending count and grouped data by date/hour
        """
        # Get total pending count
        total_pending = await self.repository.count_unprocessed()
        
        # Get pending prices grouped by date and hour
        pending_summary_data = await self.repository.get_pending_prices_summary()
        
        # Convert to Pydantic models
        pending_by_date_hour = [
            PendingPriceSummary(
                date=row["date"],
                hour=row["hour"],
                count=row["count"],
                is_simple=bool(row["is_simple"])
            )
            for row in pending_summary_data
        ]
        
        return WorkerStatusSummary(
            total_pending=total_pending,
            pending_by_date_hour=pending_by_date_hour
        )
