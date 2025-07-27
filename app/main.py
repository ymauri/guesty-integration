from fastapi import FastAPI
from api.v1.auth_router import router as auth_router
from api.v1.guesty_router import router as guesty_router
from app.api.v1.listeners_router import router as webhook_router

app = FastAPI(title="Guesty Integration")

app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(guesty_router, prefix="/api/v1/guesty", tags=["guesty"])
app.include_router(webhook_router, prefix="/api/v1/listener", tags=["listener"])
