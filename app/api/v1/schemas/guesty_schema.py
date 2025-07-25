from pydantic import BaseModel

class RegisterWebhookRequest(BaseModel):
    target_url: str
    events: list[str]