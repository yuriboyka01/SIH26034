import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from app.main import app
from app.models.user import User, UserRole
from app.models.inspection import Inspection, InspectionStatus
from app.models.inspection_image import InspectionImage, ImageType

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session_mock():
    from unittest.mock import MagicMock
    return MagicMock(spec=Session)

@pytest.fixture
def override_db(db_session_mock):
    from app.core.database import get_db
    app.dependency_overrides[get_db] = lambda: db_session_mock
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def admin_user():
    return User(id=uuid4(), email="admin@test.com", role=UserRole.ADMIN)

@pytest.fixture
def inspector_user():
    return User(id=uuid4(), email="inspector@test.com", role=UserRole.INSPECTOR)

def test_delete_image_admin_success(client, override_db, admin_user):
    from unittest.mock import patch
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    with patch("app.api.images.InspectionService"):
        response = client.delete(f"/api/inspections/{uuid4()}/images/{uuid4()}")
    
        assert response.status_code in (204, 404)
    app.dependency_overrides.pop(get_current_user, None)

def test_delete_image_inspector_forbidden(client, override_db, inspector_user):
    from unittest.mock import patch
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: inspector_user
    
    response = client.delete(f"/api/inspections/{uuid4()}/images/{uuid4()}")
    
    data = response.json()
    code = data.get("error", {}).get("code") or data.get("detail", {}).get("error", {}).get("code")
    assert code == "INSUFFICIENT_PERMISSIONS"
    app.dependency_overrides.pop(get_current_user, None)
