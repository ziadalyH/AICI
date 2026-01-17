"""
Test script to verify API endpoints work correctly.
"""
import asyncio
import httpx
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint."""
    print("Testing health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    print("✓ Health endpoint works")

def test_register_endpoint():
    """Test user registration endpoint."""
    print("\nTesting registration endpoint...")
    
    # Test successful registration
    response = client.post(
        "/api/auth/register",
        json={"username": "apiuser", "password": "apipassword123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] == True
    print(f"✓ Registration successful: {data['message']}")
    
    # Test duplicate username
    response = client.post(
        "/api/auth/register",
        json={"username": "apiuser", "password": "anotherpassword"}
    )
    assert response.status_code == 400
    print("✓ Duplicate username correctly rejected")

def test_login_endpoint():
    """Test user login endpoint."""
    print("\nTesting login endpoint...")
    
    # Test successful login
    response = client.post(
        "/api/auth/login",
        json={"username": "apiuser", "password": "apipassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["token_type"] == "bearer"
    print(f"✓ Login successful, token received: {data['token'][:20]}...")
    
    # Test invalid credentials
    response = client.post(
        "/api/auth/login",
        json={"username": "apiuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    print("✓ Invalid credentials correctly rejected")

def test_protected_endpoint():
    """Test protected endpoint with authentication."""
    print("\nTesting protected endpoint...")
    
    # First login to get a token
    response = client.post(
        "/api/auth/login",
        json={"username": "apiuser", "password": "apipassword123"}
    )
    assert response.status_code == 200
    token = response.json()["token"]
    
    # Test with valid token
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "apiuser"
    print(f"✓ Protected endpoint accessible with valid token: {data['username']}")
    
    # Test without token
    response = client.get("/api/auth/me")
    assert response.status_code == 403  # Forbidden without credentials
    print("✓ Protected endpoint correctly rejects requests without token")
    
    # Test with invalid token
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401
    print("✓ Protected endpoint correctly rejects invalid token")

def main():
    """Run all API endpoint tests."""
    print("=" * 60)
    print("Backend API Endpoints - Integration Tests")
    print("=" * 60)
    
    try:
        test_health_endpoint()
        test_register_endpoint()
        test_login_endpoint()
        test_protected_endpoint()
        
        print("\n" + "=" * 60)
        print("✓ All API endpoint tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
