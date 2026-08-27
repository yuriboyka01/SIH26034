"""Tests for authentication endpoints."""


def test_register_user(client):
    """Test successful user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["name"] == "Alice"
    assert data["user"]["role"] == "INSPECTOR"


def test_register_duplicate_email(client, registered_user):
    """Test that duplicate email registration fails."""
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Duplicate",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_login_user(client, registered_user):
    """Test successful login."""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"


def test_login_invalid_credentials(client, registered_user):
    """Test login with wrong password."""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_nonexistent_email(client):
    """Test login with email that doesn't exist."""
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user profile with valid token."""
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


def test_get_current_user_unauthorized(client):
    """Test accessing profile without authentication."""
    response = client.get("/api/auth/me")
    assert response.status_code == 403  # HTTPBearer returns 403 when no token


def test_get_current_user_invalid_token(client):
    """Test accessing profile with invalid token."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401


def test_get_current_user_malformed_uuid(client):
    """Test accessing profile with a valid token but malformed UUID subject."""
    from app.core.security import create_access_token
    token = create_access_token(subject="not-a-uuid")
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Malformed token subject."


def test_get_current_user_nonexistent_uuid(client):
    """Test accessing profile with a valid token and valid UUID but user not in DB."""
    from app.core.security import create_access_token
    import uuid
    token = create_access_token(subject=str(uuid.uuid4()))
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "User not found."
