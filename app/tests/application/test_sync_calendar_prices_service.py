import pytest
from unittest.mock import AsyncMock
from uuid import UUID
from domain.booking_experts.services import BookingExpertsClient
from application.sync_calendar_prices_service import SyncCalendarPricesService


class CalendarEntryStub:
    def __init__(self, date: str, currency: str, price: str):
        self.date = date
        self.currency = currency
        self.price = price


@pytest.mark.asyncio
async def test_sync_calendar_prices_calls_patch_master_price_list():
    # Arrange
    mock_client = AsyncMock(spec=BookingExpertsClient)
    service = SyncCalendarPricesService(booking_experts_client=mock_client)

    guesty_calendar = [
        CalendarEntryStub(date="2025-08-01", currency="EUR", price="120.00"),
        CalendarEntryStub(date="2025-08-02", currency="EUR", price="130.00"),
    ]

    price_list_id = "price-list-1"
    administration_id = "admin-1"

    # Act
    await service.sync_prices(
        price_list_id=price_list_id,
        administration_id=administration_id,
        guesty_calendar=guesty_calendar,
    )

    # Assert
    assert mock_client.patch_master_price_list.called is True

    args, kwargs = mock_client.patch_master_price_list.call_args

    assert kwargs["price_list_id"] == price_list_id
    assert kwargs["administration_id"] == administration_id

    simple_prices = kwargs["simple_prices"]
    assert len(simple_prices) == 2

    for i, entry in enumerate(guesty_calendar):
        assert simple_prices[i]["date"] == entry.date
        assert simple_prices[i]["currency"] == entry.currency
        assert simple_prices[i]["value"] == entry.price
        # Validate temp_id is a valid UUID hex string
        UUID(simple_prices[i]["temp_id"])  # Will raise if invalid
