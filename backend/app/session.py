"""
Session management for ephemeral object storage.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from threading import Lock


class Session:
    """Session model for storing ephemeral objects."""
    
    def __init__(self, session_id: str, user_id: str):
        """
        Initialize a new session.
        
        Args:
            session_id: Unique identifier for the session
            user_id: ID of the user who owns this session
        """
        self.session_id = session_id
        self.user_id = user_id
        self.ephemeral_objects: List[dict] = []
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
    
    def update_access_time(self):
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """
        Convert session to dictionary representation.
        
        Returns:
            Dictionary containing session data
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "ephemeral_objects": self.ephemeral_objects,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat()
        }


class SessionStore:
    """In-memory storage for user sessions and ephemeral objects."""
    
    def __init__(self):
        """Initialize the session store with an empty dictionary."""
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, str] = {}  # Maps user_id to session_id
        self._lock = Lock()  # Thread-safe operations
    
    def create_session(self, user_id: str) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The session ID for the newly created session
        """
        with self._lock:
            # If user already has a session, delete it first
            if user_id in self._user_sessions:
                old_session_id = self._user_sessions[user_id]
                if old_session_id in self._sessions:
                    del self._sessions[old_session_id]
            
            # Create new session
            session_id = str(uuid.uuid4())
            session = Session(session_id, user_id)
            
            self._sessions[session_id] = session
            self._user_sessions[user_id] = session_id
            
            return session_id
    
    def store_objects(self, session_id: str, objects: List[dict]) -> None:
        """
        Store ephemeral objects in a session.
        
        Args:
            session_id: The session ID
            objects: List of objects to store
            
        Raises:
            ValueError: If session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise ValueError(f"Session '{session_id}' not found")
            
            session.ephemeral_objects = objects
            session.update_access_time()
    
    def get_objects(self, session_id: str) -> List[dict]:
        """
        Retrieve ephemeral objects from a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of objects stored in the session
            
        Raises:
            ValueError: If session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise ValueError(f"Session '{session_id}' not found")
            
            session.update_access_time()
            return session.ephemeral_objects.copy()
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: The session ID
            
        Returns:
            Session object if found, None otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.update_access_time()
            return session
    
    def get_session_by_user(self, user_id: str) -> Optional[Session]:
        """
        Retrieve a session by user ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            Session object if found, None otherwise
        """
        with self._lock:
            session_id = self._user_sessions.get(user_id)
            if session_id:
                session = self._sessions.get(session_id)
                if session:
                    session.update_access_time()
                return session
            return None
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete a session and its associated data.
        
        Args:
            session_id: The session ID to delete
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                # Remove from user mapping
                if session.user_id in self._user_sessions:
                    del self._user_sessions[session.user_id]
                # Remove session
                del self._sessions[session_id]
    
    def delete_session_by_user(self, user_id: str) -> None:
        """
        Delete a session by user ID.
        
        Args:
            user_id: The user ID whose session should be deleted
        """
        with self._lock:
            session_id = self._user_sessions.get(user_id)
            if session_id:
                if session_id in self._sessions:
                    del self._sessions[session_id]
                del self._user_sessions[user_id]
    
    def clear_all(self) -> None:
        """Clear all sessions (useful for testing)."""
        with self._lock:
            self._sessions.clear()
            self._user_sessions.clear()


# Global session store instance
session_store = SessionStore()
