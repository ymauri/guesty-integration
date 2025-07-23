from pydantic import BaseModel, EmailStr
from domain.user.value_objects import UserRole

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.OWNER
