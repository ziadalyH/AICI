"""
Test the query endpoint integration.
"""
import pytest
from fastapi.testclient import TestClient
from app import app
from app.session import session_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_sessions():
    """Clean up session store before each test."""
    session_store.clear_all()
    yield
    session_store.clear_all()


def test_query_endpoint_requires_authentication():
    """Test that query endpoint requires authentication."""
    response = client.post(
        "/api/query",
        json={"question": "What is the height limit?"}
    )
    assert response.status_code in [401, 403]


def test_query_endpoint_requires_session():
    """Test that query endpoint requires an active session."""
    # Register and login with unique username
    username = f"testuser_session_{id(test_query_endpoint_requires_session)}"
    client.post("/api/auth/register", json={"username": username, "password": "testpass123"})
    login_response = client.post("/api/auth/login", json={"username": username, "password": "testpass123"})
    token = login_response.json()["token"]
    
    # Try to query without uploading objects (session exists but empty)
    response = client.post(
        "/api/query",
        json={"question": "What is the height limit?"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should succeed even with empty objects list
    assert response.status_code in [200, 503]  # 503 if AI Agent is not running


def test_query_endpoint_with_objects():
    """Test query endpoint with uploaded objects."""
    # Register and login with unique username
    username = f"testuser_objects_{id(test_query_endpoint_with_objects)}"
    client.post("/api/auth/register", json={"username": username, "password": "testpass123"})
    login_response = client.post("/api/auth/login", json={"username": username, "password": "testpass123"})
    token = login_response.json()["token"]
    
    # Upload objects
    objects = [
        {
            "id": "obj_001",
            "type": "building",
            "properties": {
                "height": 15.5,
                "width": 10.0
            }
        }
    ]
    
    upload_response = client.post(
        "/api/session/objects",
        json={"objects": objects},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert upload_response.status_code == 200
    
    # Query with objects
    response = client.post(
        "/api/query",
        json={"question": "What is the height of the building?", "top_k": 3},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should succeed or return 503 if AI Agent is not running
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "answer" in data


def test_query_endpoint_empty_question():
    """Test that empty questions are rejected."""
    # Register and login with unique username
    username = f"testuser_empty_{id(test_query_endpoint_empty_question)}"
    client.post("/api/auth/register", json={"username": username, "password": "testpass123"})
    login_response = client.post("/api/auth/login", json={"username": username, "password": "testpass123"})
    token = login_response.json()["token"]
    
    # Try to query with empty question
    response = client.post(
        "/api/query",
        json={"question": ""},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Pydantic validation will return 422 for empty string (min_length=1)
    assert response.status_code in [400, 422]


def test_query_endpoint_with_top_k():
    """Test query endpoint with custom top_k parameter."""
    # Register and login with unique username
    username = f"testuser_topk_{id(test_query_endpoint_with_top_k)}"
    client.post("/api/auth/register", json={"username": username, "password": "testpass123"})
    login_response = client.post("/api/auth/login", json={"username": username, "password": "testpass123"})
    token = login_response.json()["token"]
    
    # Query with custom top_k
    response = client.post(
        "/api/query",
        json={"question": "What are the regulations?", "top_k": 10},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should succeed or return 503 if AI Agent is not running
    assert response.status_code in [200, 503]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
