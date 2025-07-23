from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from .value_objects import UserRole

@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    hashed_password: str
    is_active: bool
    role: UserRole
    created_at: datetime
