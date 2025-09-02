from fastapi import APIRouter, Depends
from infrastructure.guesty.guesty_client import GuestyClient
from shared.cache import get_cache
from shared.dependencies import only_admins
from api.v1.schemas.guesty_schema import RegisterWebhookRequest

router = APIRouter()

@router.get("/webhooks")
async def get_webhooks(cache = Depends(get_cache)):
    guesty = GuestyClient(cache)
    return await guesty.list_webhooks()

@router.post("/webhooks/register")
async def register_webhook(webhook: RegisterWebhookRequest, cache = Depends(get_cache), role: str = Depends(only_admins)):
    guesty = GuestyClient(cache)
    return await guesty.register_webhook(webhook.target_url, webhook.events)

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str, cache = Depends(get_cache), role: str = Depends(only_admins)):
    guesty = GuestyClient(cache)
    return await guesty.remove_webhook(webhook_id)

@router.get("/listings")
async def get_listings(cache = Depends(get_cache), role: str = Depends(only_admins)):
    guesty = GuestyClient(cache)
    return await guesty.list_listings()

@router.post("/clear-auth-cache")
async def clear_auth_cache(cache = Depends(get_cache)):
    guesty = GuestyClient(cache)
    guesty.clear_auth_cache()
    return {"status": "Auth cache cleared"}
