import httpx
from typing import Any
from diskcache import Cache
from app.config import get_settings
from loguru import logger

settings = get_settings()

class GuestyClient:
    def __init__(self, cache: Cache):
        self.client_id = settings.GUESTY_CLIENT_ID
        self.client_secret = settings.GUESTY_CLIENT_SECRET
        self.auth_url = settings.GUESTY_AUTH_URL
        self.base_url = settings.GUESTY_API_BASE_URL
        self.cache = cache
        self._auth_info = self._validate_auth_info()

    def _validate_auth_info(self) -> dict:
        token_key = "guesty_auth_info"

        if token := self.cache.get(token_key):
            return token

        try:
            response = httpx.post(
                self.auth_url,
                data={
                    "grant_type": "client_credentials",
                    "scope": "open-api",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            auth_info = response.json()

            # TTL: 24h - 5min buffer = 23h55min
            self.cache.set(token_key, auth_info, expire=60 * 60 * 24 - 300)
            return auth_info

        except Exception as e:
            logger.critical(f"[Guesty] Failed to authenticate: {e}")
            raise

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._auth_info['access_token']}",
            "Content-Type": "application/json"
        }

    def _is_prod(self) -> bool:
        return settings.ENVIRONMENT == "production"

    async def list_webhooks(self) -> Any:
        if not self._is_prod():
            logger.warning("Guesty call skipped: not in production")
            return []

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/webhooks", headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def register_webhook(self, target_url: str, events: list[str]) -> Any:
        if not self._is_prod():
            logger.warning("Webhook registration skipped: not in production")
            return {}

        payload = {"url": target_url, "events": events}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/webhooks", json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def remove_webhook(self, webhook_id: str) -> bool:
        if not self._is_prod():
            logger.warning("Webhook removal skipped: not in production")
            return False

        async with httpx.AsyncClient() as client:
            resp = await client.delete(f"{self.base_url}/webhooks/{webhook_id}", headers=self._headers())
            resp.raise_for_status()
            return resp.status_code == 204

    async def list_listings(self, limit: int = 25, offset: int = 0) -> Any:
        if not self._is_prod():
            logger.warning("Guesty listings skipped: not in production")
            return []

        params = {"limit": limit, "offset": offset}
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/listings", headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()
        
    async def list_calendar(self, listing_id: str, start_date: str, end_date: str) -> Any:
        if not self._is_prod():
            logger.warning("Guesty calendar fetch skipped: not in production")
            return []

        params = {
            "startDate": start_date,
            "endDate": end_date,
            "listingIds": listing_id
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/availability-pricing/api/calendar/listings/", headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()
        
    def clear_auth_cache(self) -> None:
            try:
                self.cache.delete(self.TOKEN_KEY)
                logger.info("[Guesty] Auth cache cleared")
            except Exception as e:
                logger.warning(f"[Guesty] Failed to clear auth cache: {e}")