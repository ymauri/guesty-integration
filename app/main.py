from fastapi import FastAPI
from app.api.v1.router import router
from app.api.v1.listing_mappings_router import router as listing_mappings_router
from app.infrastructure.db.sqlite import init_db

app = FastAPI(title="Guesty Integration")

app.include_router(router, prefix="/api/v1/listener", tags=["Listener"])
app.include_router(listing_mappings_router, prefix="/api/v1/listing-mappings", tags=["Listing Mappings"])

@app.on_event("startup")
async def _init():
    await init_db()
