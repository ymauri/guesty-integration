from pydantic import BaseModel

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