import httpx
from typing import Any, Dict, List
from loguru import logger
from app.config import get_settings
from domain.booking_experts.services import BookingExpertsClient

settings = get_settings()

class APIBookingExpertsClient(BookingExpertsClient):
    def __init__(self):
        self.base_url = settings.BOOKING_EXPERTS_API_BASE_URL
        self.headers = {
            "accept": "application/vnd.api+json",
            "content-type": "application/vnd.api+json",
            "X-API-KEY": settings.BOOKING_EXPERTS_API_KEY
        }

    async def patch_master_price_list(
        self,
        price_list_id: str,
        administration_id: str,
        simple_prices: List[Dict] = None,
        complex_prices: List[Dict] = None,
    ) -> Any:
        url = (
            f"{self.base_url}/administrations/{administration_id}"
            f"/master_price_lists/{price_list_id}"
        )

        data: Dict[str, Any] = {
            "data": {
                "id": price_list_id,
                "type": "master_price_list",
            }
        }

        included = []
        relationships = {}

        if simple_prices:
            relationships["simple_prices"] = {
                "data": [
                    {
                        "type": "simple_price",
                        "meta": {"temp_id": sp["temp_id"], "method": "create"},
                    }
                    for sp in simple_prices
                ]
            }

            included += [
                {
                    "type": "simple_price",
                    "attributes": {
                        "date": sp["date"],
                        "price": {
                            "currency": sp["currency"],
                            "value": str(sp["value"]),
                        },
                    },
                    "meta": {"temp_id": sp["temp_id"]},
                }
                for sp in simple_prices
            ]

        if complex_prices:
            relationships["complex_prices"] = {
                "data": [
                    {
                        "type": "complex_price",
                        "meta": {"temp_id": cp["temp_id"], "method": "create"},
                    }
                    for cp in complex_prices
                ]
            }

            included += [
                {
                    "type": "complex_price",
                    "attributes": {
                        "arrival_date": cp["arrival_date"],
                        "length_of_stay": cp["length_of_stay"],
                        "price": {
                            "currency": cp["currency"],
                            "value": str(cp["value"]),
                        },
                    },
                    "meta": {"temp_id": cp["temp_id"]},
                }
                for cp in complex_prices
            ]

        if relationships:
            data["data"]["relationships"] = relationships
        if included:
            data["included"] = included

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(
                f"[BookingExperts] Failed to patch price list {price_list_id}: {e}"
            )
            if e.response is not None:
                logger.debug(f"Response: {e.response.text}")
            raise
