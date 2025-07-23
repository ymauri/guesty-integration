from abc import ABC, abstractmethod
from .entities import User
from typing import Optional
from uuid import UUID

class UserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    def create_user(self, user: User) -> None:
        pass
