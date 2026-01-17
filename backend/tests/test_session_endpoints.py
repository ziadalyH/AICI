"""
Test session management endpoints.
"""
import pytest
import os
from fastapi.testclient import TestClient
from app import app
from app.database import db
from app.session import session_store


client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up database and session store before each test."""
    # Clear session store
    session_store.clear_all()
    
    # Clean up test database if it exists
    if os.path.exists("users.db"):
        # Delete all users from database
        import sqlite3
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()
    
    yield
    
    # Clean up after test
    session_store.clear_all()


def test_upload_objects_requires_authentication():
    """Test that uploading objects requires authentication."""
    response = client.post(
        "/api/session/objects",
        json={"objects": [{"id": "test1", "value": "data"}]}
    )
    assert response.status_code == 403  # Forbidden without auth


def test_get_objects_requires_authentication():
    """Test that retrieving objects requires authentication."""
    response = client.get("/api/session/objects")
    assert response.status_code == 403  # Forbidden without auth


def test_upload_and_retrieve_objects():
    """Test uploading and retrieving objects with authentication."""
    # Register and login
    username = "testuser_session"
    password = "testpass123"
    
    # Register
    register_response = client.post(
        "/api/auth/register",
        json={"username": username, "password": password}
    )
    assert register_response.status_code == 201
    
    # Login
    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password}
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    # Upload objects
    test_objects = [
        {"id": "obj1", "type": "test", "value": 100},
        {"id": "obj2", "type": "test", "value": 200}
    ]
    
    upload_response = client.post(
        "/api/session/objects",
        json={"objects": test_objects},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["success"] is True
    assert "session_id" in upload_data
    
    # Retrieve objects
    get_response = client.get(
        "/api/session/objects",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["success"] is True
    assert len(get_data["objects"]) == 2
    assert get_data["objects"] == test_objects


def test_update_objects():
    """Test updating objects in a session."""
    # Register and login
    username = "testuser_update"
    password = "testpass123"
    
    client.post("/api/auth/register", json={"username": username, "password": password})
    login_response = client.post("/api/auth/login", json={"username": username, "password": password})
    token = login_response.json()["token"]
    
    # Upload initial objects
    initial_objects = [{"id": "obj1", "value": 100}]
    client.post(
        "/api/session/objects",
        json={"objects": initial_objects},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Update with new objects
    updated_objects = [
        {"id": "obj1", "value": 150},
        {"id": "obj2", "value": 200}
    ]
    client.post(
        "/api/session/objects",
        json={"objects": updated_objects},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Retrieve and verify updated objects
    get_response = client.get(
        "/api/session/objects",
        headers={"Authorization": f"Bearer {token}"}
    )
    get_data = get_response.json()
    assert len(get_data["objects"]) == 2
    assert get_data["objects"] == updated_objects


def test_empty_objects_list():
    """Test uploading an empty objects list."""
    # Register and login
    username = "testuser_empty"
    password = "testpass123"
    
    client.post("/api/auth/register", json={"username": username, "password": password})
    login_response = client.post("/api/auth/login", json={"username": username, "password": password})
    token = login_response.json()["token"]
    
    # Upload empty list
    upload_response = client.post(
        "/api/session/objects",
        json={"objects": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert upload_response.status_code == 200
    
    # Retrieve and verify empty list
    get_response = client.get(
        "/api/session/objects",
        headers={"Authorization": f"Bearer {token}"}
    )
    get_data = get_response.json()
    assert get_data["objects"] == []


def test_session_created_on_login():
    """Test that a session is created when user logs in."""
    # Register and login
    username = "testuser_login_session"
    password = "testpass123"
    
    client.post("/api/auth/register", json={"username": username, "password": password})
    login_response = client.post("/api/auth/login", json={"username": username, "password": password})
    token = login_response.json()["token"]
    
    # Verify session exists by retrieving objects (should return empty list, not error)
    get_response = client.get(
        "/api/session/objects",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["objects"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
