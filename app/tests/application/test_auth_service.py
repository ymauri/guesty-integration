import pytest
from uuid import uuid4
from datetime import datetime
from domain.user.entities import User
from domain.user.value_objects import UserRole
from application.auth_service import AuthService
from shared.exceptions import UnauthorizedException
from tests.fakers.fake_user_repository import FakeUserRepository
from application.auth_service import pwd_context

@pytest.fixture
def test_user():
    return User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password=pwd_context.hash("StrongPassword123"),
        is_active=True,
        role=UserRole.ADMIN,
        created_at=datetime.utcnow()
    )


def test_login_success(test_user):
    repo = FakeUserRepository(users={test_user.email: test_user})
    auth = AuthService(user_repository=repo)

    token = auth.login("admin@example.com", "StrongPassword123")
    assert isinstance(token, str)
    assert token.count('.') == 2


def test_login_wrong_password(test_user):
    repo = FakeUserRepository(users={test_user.email: test_user})
    auth = AuthService(user_repository=repo)

    with pytest.raises(UnauthorizedException):
        auth.login("admin@example.com", "WrongPassword")


def test_login_unknown_user():
    repo = FakeUserRepository(users={})
    auth = AuthService(user_repository=repo)

    with pytest.raises(UnauthorizedException):
        auth.login("ghost@example.com", "whatever")
