import types
import pytest
from dataclasses import dataclass

# Import the module under test (make sure this matches your file name/path)
import app.application.sync_calendar_prices_service as svc


# --------------------------
# Test helpers & fakes
# --------------------------

@dataclass
class Day:
    date: str
    listingId: str
    price: float
    currency: str


class DummySettings:
    BOOKING_EXPERTS_MASTER_PRICE_LIST_ID = "pl_123"
    BOOKING_EXPERTS_ADMINISTRATION_ID = "adm_456"


class FakeClient:
    def __init__(self, fail_after=None, exception=None):
        self.calls = []
        self.fail_after = fail_after
        self.exception = exception or Exception("boom")

    async def patch_master_price_list(self, *, price_list_id, administration_id, simple_prices, complex_prices):
        # Optional failure injection
        if self.fail_after is not None and len(self.calls) >= self.fail_after:
            raise self.exception

        self.calls.append({
            "price_list_id": price_list_id,
            "administration_id": administration_id,
            "simple_prices": simple_prices,
            "complex_prices": complex_prices,
        })


def make_days(n, listing="allow-1"):
    return [Day(date=f"2025-12-{(i%28)+1:02d}", listingId=listing, price=100 + i, currency="EUR") for i in range(n)]


def bind_noop_rate_gate(service):
    async def _noop(self):
        return
    # Bind as if it were a method to avoid awaiting any real gating/sleep in tests
    service._rate_gate = types.MethodType(_noop, service)


@pytest.fixture
def service_and_client(monkeypatch):
    # Patch module-level config and allow-list
    monkeypatch.setattr(svc, "settings", DummySettings(), raising=False)
    monkeypatch.setattr(svc, "guesty_listings", lambda: {"allow-1"}, raising=False)
    # Use a small batch size to make tests deterministic
    monkeypatch.setattr(svc, "BATCH_SIZE", 10, raising=False)

    client = FakeClient()
    service = svc.SyncCalendarPricesService(client)

    # Avoid sleeping/rate gating during tests
    bind_noop_rate_gate(service)

    return service, client


# --------------------------
# Tests
# --------------------------

@pytest.mark.asyncio
async def test_batches_simple_prices(service_and_client, monkeypatch):
    service, client = service_and_client

    days = make_days(23, listing="allow-1")  # 23 items, BATCH_SIZE=10 => 3 calls: 10,10,3
    await service.sync_prices(days, is_simple=True)

    assert len(client.calls) == 3

    # First two calls: 10 simple items, no complex
    for call in client.calls[:2]:
        assert len(call["simple_prices"]) == 10
        assert call["complex_prices"] == []
        # payload keys (subset) check
        assert all(set(p.keys()) >= {"date", "value", "currency"} for p in call["simple_prices"])

    # Last call: 3 items
    last = client.calls[-1]
    assert len(last["simple_prices"]) == 3
    assert last["complex_prices"] == []
    assert all(set(p.keys()) >= {"date", "value", "currency"} for p in last["simple_prices"])


@pytest.mark.asyncio
async def test_batches_complex_prices(service_and_client):
    service, client = service_and_client

    days = make_days(21, listing="allow-1")  # 21 items => 3 calls: 10,10,1
    await service.sync_prices(days, is_simple=False)

    assert len(client.calls) == 3

    # First two calls: 10 complex items
    for call in client.calls[:2]:
        assert call["simple_prices"] == []
        assert len(call["complex_prices"]) == 10
        assert all(set(p.keys()) >= {"arrival_date", "value", "currency"} for p in call["complex_prices"])

    # Last call: 1 item
    last = client.calls[-1]
    assert last["simple_prices"] == []
    assert len(last["complex_prices"]) == 1
    assert set(last["complex_prices"][0].keys()) >= {"arrival_date", "value", "currency"}


@pytest.mark.asyncio
async def test_skips_unallowed_listings(monkeypatch):
    # Patch allow-list to NOT include our listing
    monkeypatch.setattr(svc, "settings", DummySettings(), raising=False)
    monkeypatch.setattr(svc, "guesty_listings", lambda: {"allow-1"}, raising=False)
    monkeypatch.setattr(svc, "BATCH_SIZE", 10, raising=False)

    client = FakeClient()
    service = svc.SyncCalendarPricesService(client)
    bind_noop_rate_gate(service)

    days = make_days(15, listing="blocked")  # all blocked => no API calls
    await service.sync_prices(days, is_simple=True)

    assert len(client.calls) == 0, "Expected no calls when all listings are filtered out"


@pytest.mark.asyncio
async def test_empty_calendar_noop(service_and_client):
    service, client = service_and_client

    await service.sync_prices([], is_simple=True)
    assert len(client.calls) == 0

    await service.sync_prices(None, is_simple=False)
    assert len(client.calls) == 0


@pytest.mark.asyncio
async def test_error_notification_on_exception(monkeypatch):
    monkeypatch.setattr(svc, "settings", DummySettings(), raising=False)
    monkeypatch.setattr(svc, "guesty_listings", lambda: {"allow-1"}, raising=False)
    monkeypatch.setattr(svc, "BATCH_SIZE", 10, raising=False)

    # Capture notification
    noticed = {}
    def fake_notify(subject, body):
        noticed["subject"] = subject
        noticed["body"] = body
    monkeypatch.setattr(svc, "send_execution_email", fake_notify, raising=False)

    # Client fails on first call
    client = FakeClient(fail_after=0, exception=TimeoutError("BEX timeout"))
    service = svc.SyncCalendarPricesService(client)
    bind_noop_rate_gate(service)

    days = make_days(12, listing="allow-1")

    # Service should catch and notify (adjust if your service re-raises)
    await service.sync_prices(days, is_simple=True)

    assert noticed.get("subject") == "Error Syncing Prices"
    assert "timeout" in noticed.get("body", "").lower() or "timed out" in noticed.get("body", "").lower()
    assert len(client.calls) == 0
