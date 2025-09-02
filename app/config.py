from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    GUESTY_CLIENT_ID: str
    GUESTY_CLIENT_SECRET: str
    GUESTY_AUTH_URL: str
    GUESTY_API_BASE_URL: str
    BOOKING_EXPERTS_API_KEY: str
    BOOKING_EXPERTS_API_BASE_URL: str
    BOOKING_EXPERTS_ADMINISTRATION_ID: str
    BOOKING_EXPERTS_MASTER_PRICE_LIST_ID: str
    ENVIRONMENT: str = "development"
    EMAIL_SENDER: str
    EMAIL_RECEIVER: str
    EMAIL_PASSWORD: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
