"""Tests for inspection endpoints."""


def test_create_inspection(client, auth_headers):
    """Test creating a new inspection."""
    response = client.post(
        "/api/inspections",
        json={"product_name": "Test Rice", "brand": "Test Brand"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product_name"] == "Test Rice"
    assert data["brand"] == "Test Brand"
    assert data["status"] == "CREATED"
    assert data["inspection_number"].startswith("INS-")
    assert "id" in data


def test_create_inspection_unauthorized(client):
    """Test creating inspection without authentication."""
    response = client.post(
        "/api/inspections",
        json={"product_name": "Test", "brand": "Brand"},
    )
    assert response.status_code == 403


def test_list_inspections(client, auth_headers):
    """Test listing inspections."""
    # Create two inspections
    client.post(
        "/api/inspections",
        json={"product_name": "Product 1", "brand": "Brand 1"},
        headers=auth_headers,
    )
    client.post(
        "/api/inspections",
        json={"product_name": "Product 2", "brand": "Brand 2"},
        headers=auth_headers,
    )

    response = client.get("/api/inspections", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_inspection(client, auth_headers):
    """Test getting a specific inspection."""
    # Create inspection
    create_resp = client.post(
        "/api/inspections",
        json={"product_name": "Specific Product", "brand": "Specific Brand"},
        headers=auth_headers,
    )
    inspection_id = create_resp.json()["id"]

    response = client.get(f"/api/inspections/{inspection_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "Specific Product"
    assert data["images"] == []


def test_get_inspection_not_found(client, auth_headers):
    """Test getting a non-existent inspection."""
    response = client.get(
        "/api/inspections/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_get_inspection_malformed_uuid(client, auth_headers):
    """Test getting an inspection with malformed UUID."""
    response = client.get(
        "/api/inspections/not-a-uuid",
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_dashboard_stats(client, auth_headers):
    """Test dashboard statistics."""
    # Create an inspection
    client.post(
        "/api/inspections",
        json={"product_name": "Stats Product", "brand": "Stats Brand"},
        headers=auth_headers,
    )

    response = client.get("/api/dashboard/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["created"] == 1
