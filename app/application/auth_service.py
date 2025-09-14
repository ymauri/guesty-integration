from domain.user.services import UserRepository
from shared.exceptions import UnauthorizedException
from passlib.context import CryptContext
from shared.security import create_access_token
from domain.user.entities import User
from domain.user.value_objects import UserRole
from uuid import uuid4
from datetime import datetime, timedelta
from config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def login(self, email: str, password: str) -> str:
        user = self.user_repository.get_by_email(email)
        if not user or not user.is_active:
            raise UnauthorizedException("Invalid credentials")
        
        if not pwd_context.verify(password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        
        return create_access_token(user.id, user.email, user.role)
    
    def register_user(self, email: str, password: str, role: UserRole = UserRole.OWNER) -> None:
        hashed_password = pwd_context.hash(password)
        user = User(
            id=uuid4(),
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            role=role,
            created_at=datetime.now()
        )
        self.user_repository.create_user(user)