from pydantic import BaseModel, EmailStr
from domain.user.value_objects import UserRole

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.OWNER

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"