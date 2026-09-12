"""
Test configuration and fixtures.

Uses SQLite in-memory for fast, zero-config test execution.
"""

import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import Base, get_db
from app.main import app


# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def upload_dir():
    """Provide a temporary upload directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the settings
        from app.core.config import settings
        original = settings.UPLOAD_DIR
        settings.UPLOAD_DIR = tmpdir
        yield tmpdir
        settings.UPLOAD_DIR = original


@pytest.fixture
def registered_user(client):
    """Register a test user and return (user_data, token)."""
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    return data["user"], data["access_token"]


@pytest.fixture
def auth_headers(registered_user):
    """Return authorization headers for the registered test user."""
    _, token = registered_user
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_auth_headers(client):
    """Return authorization headers for an admin user."""
    from app.models.user import User, UserRole
    # Register
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Admin User",
            "email": "admin@example.com",
            "password": "testpassword123",
        },
    )
    data = response.json()
    user_id = data["user"]["id"]
    token = data["access_token"]
    
    import uuid
    user_id_uuid = uuid.UUID(user_id)
    # Make admin
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id_uuid).first()
        user.role = UserRole.ADMIN
        db.commit()
    finally:
        db.close()
        
    return {"Authorization": f"Bearer {token}"}
