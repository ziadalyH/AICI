"""
Debug test to see the actual error.
"""
import os
import traceback
from fastapi.testclient import TestClient

# Remove existing database for fresh test
if os.path.exists("users.db"):
    os.remove("users.db")

# Import after removing DB
from app import app

client = TestClient(app)

try:
    print("Testing registration...")
    response = client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "testpassword123"}
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 201:
        print("\nTrying to get more details by importing directly...")
        from app.database import db
        try:
            user = db.create_user("testuser2", "testpassword123")
            print(f"Direct creation worked: {user}")
        except Exception as e:
            print(f"Direct creation failed: {e}")
            traceback.print_exc()
            
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
