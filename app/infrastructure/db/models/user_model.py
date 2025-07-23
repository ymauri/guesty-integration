from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.sql import func
from uuid import uuid4
from infrastructure.db.session import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
