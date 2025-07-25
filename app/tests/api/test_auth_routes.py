import pytest
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4
from datetime import datetime
from infrastructure.db.session import Base, engine, SessionLocal
from infrastructure.db.models.user_model import UserModel
from domain.user.value_objects import UserRole
from application.auth_service import pwd_context
from shared.dependencies import get_current_user_role
from tests.fakers.fake_user_role import admin_user

client = TestClient(app)
app.dependency_overrides[get_current_user_role] = admin_user


# --- Test DB setup and teardown (with SQLite) ---
@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# --- Helper function to insert a user ---
def insert_user(email: str, password: str, role: UserRole = UserRole.ADMIN):
    db = SessionLocal()
    user = UserModel(
        id=str(uuid4()),
        email=email,
        hashed_password=pwd_context.hash(password),
        is_active=True,
        role=role.value,
        created_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.close()


# --- Tests ---
def test_register_success():
    response = client.post("/api/v1/register", json={
        "email": "newuser@example.com",
        "password": "newpassword123",
        "role": "owner"
    })
    assert response.status_code == 201
    assert response.json() == {"message": "User registered successfully"}


def test_register_duplicate_user():
    insert_user("existing@example.com", "pass123")
    response = client.post("/api/v1/register", json={
        "email": "existing@example.com",
        "password": "anotherpass",
        "role": "admin"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success():
    insert_user("admin@example.com", "mypassword")
    response = client.post("/api/v1/login", json={
        "email": "admin@example.com",
        "password": "mypassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    insert_user("fail@example.com", "correctpass")
    response = client.post("/api/v1/login", json={
        "email": "fail@example.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
