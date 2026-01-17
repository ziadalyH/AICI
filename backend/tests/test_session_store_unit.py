"""
Unit tests for the SessionStore class to verify task 3.1 implementation.
"""
import pytest
from app.session import SessionStore, Session


def test_session_model_creation():
    """Test that Session model has all required attributes."""
    session = Session("test-session-id", "test-user-id")
    
    # Verify all required attributes exist
    assert hasattr(session, 'session_id')
    assert hasattr(session, 'user_id')
    assert hasattr(session, 'ephemeral_objects')
    assert hasattr(session, 'created_at')
    assert hasattr(session, 'last_accessed')
    
    # Verify initial values
    assert session.session_id == "test-session-id"
    assert session.user_id == "test-user-id"
    assert session.ephemeral_objects == []
    assert session.created_at is not None
    assert session.last_accessed is not None


def test_session_store_create_session():
    """Test SessionStore.create_session method."""
    store = SessionStore()
    
    # Create a session
    session_id = store.create_session("user123")
    
    # Verify session was created
    assert session_id is not None
    assert isinstance(session_id, str)
    
    # Verify session can be retrieved
    session = store.get_session(session_id)
    assert session is not None
    assert session.user_id == "user123"
    assert session.ephemeral_objects == []


def test_session_store_store_objects():
    """Test SessionStore.store_objects method."""
    store = SessionStore()
    
    # Create a session
    session_id = store.create_session("user123")
    
    # Store objects
    test_objects = [
        {"id": "obj1", "value": 100},
        {"id": "obj2", "value": 200}
    ]
    store.store_objects(session_id, test_objects)
    
    # Verify objects were stored
    session = store.get_session(session_id)
    assert session.ephemeral_objects == test_objects


def test_session_store_get_objects():
    """Test SessionStore.get_objects method."""
    store = SessionStore()
    
    # Create a session and store objects
    session_id = store.create_session("user123")
    test_objects = [{"id": "obj1", "value": 100}]
    store.store_objects(session_id, test_objects)
    
    # Retrieve objects
    retrieved_objects = store.get_objects(session_id)
    
    # Verify objects match
    assert retrieved_objects == test_objects


def test_session_store_delete_session():
    """Test SessionStore.delete_session method."""
    store = SessionStore()
    
    # Create a session
    session_id = store.create_session("user123")
    
    # Verify session exists
    assert store.get_session(session_id) is not None
    
    # Delete session
    store.delete_session(session_id)
    
    # Verify session no longer exists
    assert store.get_session(session_id) is None


def test_session_store_uses_dictionary():
    """Test that SessionStore uses Python dictionary for in-memory storage."""
    store = SessionStore()
    
    # Verify internal storage is a dictionary
    assert hasattr(store, '_sessions')
    assert isinstance(store._sessions, dict)


def test_session_store_update_objects():
    """Test updating objects in a session (Requirements 2.3)."""
    store = SessionStore()
    
    # Create session and store initial objects
    session_id = store.create_session("user123")
    initial_objects = [{"id": "obj1", "value": 100}]
    store.store_objects(session_id, initial_objects)
    
    # Update with new objects
    updated_objects = [
        {"id": "obj1", "value": 150},
        {"id": "obj2", "value": 200}
    ]
    store.store_objects(session_id, updated_objects)
    
    # Verify objects were replaced
    retrieved_objects = store.get_objects(session_id)
    assert retrieved_objects == updated_objects
    assert len(retrieved_objects) == 2


def test_session_store_multiple_users():
    """Test that multiple users can have separate sessions."""
    store = SessionStore()
    
    # Create sessions for two users
    session_id_1 = store.create_session("user1")
    session_id_2 = store.create_session("user2")
    
    # Store different objects for each user
    objects_1 = [{"id": "obj1", "user": "user1"}]
    objects_2 = [{"id": "obj2", "user": "user2"}]
    
    store.store_objects(session_id_1, objects_1)
    store.store_objects(session_id_2, objects_2)
    
    # Verify each user has their own objects
    assert store.get_objects(session_id_1) == objects_1
    assert store.get_objects(session_id_2) == objects_2


def test_session_cleanup_on_delete():
    """Test that session cleanup removes all associated data (Requirements 2.5)."""
    store = SessionStore()
    
    # Create session with objects
    session_id = store.create_session("user123")
    test_objects = [{"id": "obj1", "value": 100}]
    store.store_objects(session_id, test_objects)
    
    # Delete session
    store.delete_session(session_id)
    
    # Verify session and objects are removed
    assert store.get_session(session_id) is None
    
    # Attempting to get objects should raise ValueError
    with pytest.raises(ValueError):
        store.get_objects(session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
