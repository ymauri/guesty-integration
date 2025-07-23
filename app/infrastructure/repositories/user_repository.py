from domain.user.services import UserRepository
from domain.user.entities import User
from domain.user.value_objects import UserRole
from infrastructure.db.models.user_model import UserModel
from infrastructure.db.session import SessionLocal
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.exc import IntegrityError

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal()

    def get_by_email(self, email: str) -> Optional[User]:
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._map_to_entity(db_user) if db_user else None

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        db_user = self.db.query(UserModel).filter(UserModel.id == str(user_id)).first()
        return self._map_to_entity(db_user) if db_user else None

    def _map_to_entity(self, db_user: UserModel) -> User:
        return User(
            id=UUID(db_user.id),
            email=db_user.email,
            hashed_password=db_user.hashed_password,
            is_active=db_user.is_active,
            role=UserRole(db_user.role),
            created_at=db_user.created_at or datetime.utcnow(),
        )
    
    def create_user(self, user: User) -> None:
        db_user = UserModel(
            id=str(user.id),
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            role=user.role.value,
            created_at=user.created_at
        )
        self.db.add(db_user)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ValueError("User with this email already exists")
