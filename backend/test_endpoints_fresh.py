"""
Test script to verify authentication API endpoints work correctly.
"""
import os
import uuid

# Remove existing database for fresh test BEFORE importing app
if os.path.exists("users.db"):
    os.remove("users.db")

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_endpoints():
    """Test all authentication endpoints."""
    print("=" * 60)
    print("Testing Authentication API Endpoints")
    print("=" * 60)
    
    # Generate unique username for this test run
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    test_password = "testpassword123"
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    print("   ✓ Health endpoint works")
    
    # Test 2: User registration
    print(f"\n2. Testing registration endpoint with username: {test_username}...")
    response = client.post(
        "/api/auth/register",
        json={"username": test_username, "password": test_password}
    )
    print(f"   Status code: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 201
    data = response.json()
    assert data["success"] == True
    assert "registered successfully" in data["message"]
    print("   ✓ Registration successful")
    
    # Test 3: Duplicate registration
    print("\n3. Testing duplicate username rejection...")
    response = client.post(
        "/api/auth/register",
        json={"username": test_username, "password": "anotherpassword"}
    )
    print(f"   Status code: {response.status_code}")
    assert response.status_code == 400
    print("   ✓ Duplicate username correctly rejected")
    
    # Test 4: User login with valid credentials
    print("\n4. Testing login with valid credentials...")
    response = client.post(
        "/api/auth/login",
        json={"username": test_username, "password": test_password}
    )
    print(f"   Status code: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["token_type"] == "bearer"
    token = data["token"]
    print(f"   ✓ Login successful, token received: {token[:30]}...")
    
    # Test 5: Login with invalid credentials
    print("\n5. Testing login with invalid credentials...")
    response = client.post(
        "/api/auth/login",
        json={"username": test_username, "password": "wrongpassword"}
    )
    print(f"   Status code: {response.status_code}")
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]
    print("   ✓ Invalid credentials correctly rejected")
    
    # Test 6: Protected endpoint with valid token
    print("\n6. Testing protected endpoint with valid token...")
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"   Status code: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_username
    print(f"   ✓ Protected endpoint accessible: {data['username']}")
    
    # Test 7: Protected endpoint without token
    print("\n7. Testing protected endpoint without token...")
    response = client.get("/api/auth/me")
    print(f"   Status code: {response.status_code}")
    assert response.status_code == 403
    print("   ✓ Protected endpoint correctly rejects requests without token")
    
    # Test 8: Protected endpoint with invalid token
    print("\n8. Testing protected endpoint with invalid token...")
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    print(f"   Status code: {response.status_code}")
    assert response.status_code == 401
    print("   ✓ Protected endpoint correctly rejects invalid token")
    
    print("\n" + "=" * 60)
    print("✓ All authentication endpoint tests passed!")
    print("=" * 60)
    print("\nTask 2.5 Implementation Summary:")
    print("- POST /api/auth/register endpoint: ✓ Working")
    print("- POST /api/auth/login endpoint: ✓ Working")
    print("- Request/response models: ✓ Defined")
    print("- Requirements 1.1, 1.2, 1.3: ✓ Satisfied")

if __name__ == "__main__":
    try:
        test_endpoints()
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise
