from pydantic import BaseModel
from typing import List

class RegisterWebhookRequest(BaseModel):
    target_url: str
    events: list[str]

class Day(BaseModel):
    date: str
    listingId: str
    price: float
    status: str
    currency: str

class ListingCalendarUpdatedResponse(BaseModel):       
    calendar: list[Day]
    event: str = "listing.calendar.updated"

class PendingPriceSummary(BaseModel):
    date: str  # YYYY-MM-DD
    hour: int  # 0-23
    count: int
    is_simple: bool

class WorkerStatusSummary(BaseModel):
    total_pending: int
    pending_by_date_hour: List[PendingPriceSummary]

class ListingPriceListMapping(BaseModel):
    id: int
    guesty_listing_id: str
    booking_experts_price_list_id: str
    is_active: bool
    created_at: str
    updated_at: str

class CreateListingMappingRequest(BaseModel):
    guesty_listing_id: str
    booking_experts_price_list_id: str

class UpdateListingMappingRequest(BaseModel):
    booking_experts_price_list_id: str