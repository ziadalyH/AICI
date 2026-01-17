"""
Manual test script to verify authentication endpoints.
"""
import sys
from app.database import db
from app.auth import create_access_token, authenticate_user, verify_token

def test_user_creation():
    """Test user creation and password hashing."""
    print("Testing user creation...")
    try:
        # Create a test user
        user = db.create_user("testuser", "testpassword123")
        print(f"✓ User created: {user.username} (ID: {user.id})")
        
        # Verify password hashing
        assert user.password_hash != "testpassword123", "Password should be hashed"
        print("✓ Password is properly hashed")
        
        # Verify password
        is_valid = db.verify_password("testpassword123", user.password_hash)
        assert is_valid, "Password verification should succeed"
        print("✓ Password verification works")
        
        # Test wrong password
        is_invalid = db.verify_password("wrongpassword", user.password_hash)
        assert not is_invalid, "Wrong password should fail verification"
        print("✓ Wrong password correctly rejected")
        
        return user
    except Exception as e:
        print(f"✗ User creation failed: {e}")
        return None

def test_authentication(username, password):
    """Test user authentication."""
    print("\nTesting authentication...")
    try:
        # Test valid credentials
        user = authenticate_user(username, password)
        assert user is not None, "Authentication should succeed with valid credentials"
        print(f"✓ Authentication successful for user: {user.username}")
        
        # Test invalid credentials
        invalid_user = authenticate_user(username, "wrongpassword")
        assert invalid_user is None, "Authentication should fail with invalid password"
        print("✓ Invalid credentials correctly rejected")
        
        return user
    except Exception as e:
        print(f"✗ Authentication test failed: {e}")
        return None

def test_jwt_tokens(user):
    """Test JWT token generation and validation."""
    print("\nTesting JWT tokens...")
    try:
        # Generate token
        token = create_access_token(user.id, user.username)
        assert token is not None and len(token) > 0, "Token should be generated"
        print(f"✓ JWT token generated: {token[:20]}...")
        
        # Verify token
        verified_user = verify_token(token)
        assert verified_user is not None, "Token verification should succeed"
        assert verified_user.id == user.id, "Verified user should match original user"
        print(f"✓ Token verified successfully for user: {verified_user.username}")
        
        # Test invalid token
        try:
            verify_token("invalid.token.here")
            print("✗ Invalid token should raise exception")
        except Exception:
            print("✓ Invalid token correctly rejected")
        
        return True
    except Exception as e:
        print(f"✗ JWT token test failed: {e}")
        return False

def main():
    """Run all authentication tests."""
    print("=" * 60)
    print("Backend API Authentication System - Manual Tests")
    print("=" * 60)
    
    # Test user creation
    user = test_user_creation()
    if not user:
        print("\n✗ Tests failed at user creation")
        sys.exit(1)
    
    # Test authentication
    authenticated_user = test_authentication("testuser", "testpassword123")
    if not authenticated_user:
        print("\n✗ Tests failed at authentication")
        sys.exit(1)
    
    # Test JWT tokens
    jwt_success = test_jwt_tokens(user)
    if not jwt_success:
        print("\n✗ Tests failed at JWT token validation")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All authentication tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
