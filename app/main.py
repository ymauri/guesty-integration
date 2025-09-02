from fastapi import FastAPI
from app.api.v1.auth_router import router as auth_router
from app.api.v1.guesty_router import router as guesty_router
from app.api.v1.listeners_router import router as listeners_router

app = FastAPI(title="Guesty Integration")

app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(guesty_router, prefix="/api/v1/guesty", tags=["guesty"])
app.include_router(listeners_router, prefix="/api/v1/listener", tags=["listener"])
