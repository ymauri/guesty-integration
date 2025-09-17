from fastapi import FastAPI
from app.api.v1.router import router

app = FastAPI(title="Guesty Integration")

app.include_router(router, prefix="/api/v1/listener", tags=["Listener"])
