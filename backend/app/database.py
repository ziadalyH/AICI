"""
Database management using MongoDB.
"""
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from passlib.context import CryptContext
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError

from .models import User


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Database:
    """MongoDB database manager for user and object storage."""
    
    def __init__(self, connection_string: str = None, db_name: str = None):
        """
        Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection string (defaults to env var or localhost)
            db_name: Database name (defaults to env var or 'hybrid_rag_qa')
        """
        if connection_string is None:
            connection_string = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
        if db_name is None:
            db_name = os.getenv("MONGODB_DB_NAME", "hybrid_rag_qa")
            
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.users_collection = self.db["users"]
        self.objects_collection = self.db["user_objects"]
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema with indexes."""
        # Create unique index on username
        self.users_collection.create_index([("username", ASCENDING)], unique=True)
        
        # Create index on user_id for objects collection
        self.objects_collection.create_index([("user_id", ASCENDING)])
    
    def create_user(self, username: str, password: str) -> User:
        """
        Create a new user with hashed password.
        
        Args:
            username: The username for the new user
            password: The plain text password to hash
            
        Returns:
            User: The created user object
            
        Raises:
            ValueError: If username already exists
        """
        # Check if user already exists
        if self.get_user_by_username(username):
            raise ValueError(f"Username '{username}' already exists")
        
        user_id = str(uuid.uuid4())
        password_hash = pwd_context.hash(password)
        created_at = datetime.utcnow()
        
        user_doc = {
            "_id": user_id,
            "username": username,
            "password_hash": password_hash,
            "created_at": created_at
        }
        
        try:
            self.users_collection.insert_one(user_doc)
        except DuplicateKeyError:
            raise ValueError(f"Username '{username}' already exists")
        
        return User(
            id=user_id,
            username=username,
            password_hash=password_hash,
            created_at=created_at
        )
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by username.
        
        Args:
            username: The username to search for
            
        Returns:
            User object if found, None otherwise
        """
        user_doc = self.users_collection.find_one({"username": username})
        
        if user_doc:
            return User(
                id=user_doc["_id"],
                username=user_doc["username"],
                password_hash=user_doc["password_hash"],
                created_at=user_doc["created_at"]
            )
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by ID.
        
        Args:
            user_id: The user ID to search for
            
        Returns:
            User object if found, None otherwise
        """
        user_doc = self.users_collection.find_one({"_id": user_id})
        
        if user_doc:
            return User(
                id=user_doc["_id"],
                username=user_doc["username"],
                password_hash=user_doc["password_hash"],
                created_at=user_doc["created_at"]
            )
        return None
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: The plain text password
            hashed_password: The hashed password to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: The plain text password to hash
            
        Returns:
            The hashed password
        """
        return pwd_context.hash(password)
    
    def save_user_objects(self, user_id: str, objects: List[Dict[str, Any]]) -> None:
        """
        Save or update objects for a user.
        
        Args:
            user_id: The user ID
            objects: List of objects to save (stored as-is in MongoDB)
        """
        timestamp = datetime.utcnow()
        
        # Use upsert to update if exists, insert if not
        self.objects_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "objects": objects,
                    "updated_at": timestamp
                },
                "$setOnInsert": {
                    "created_at": timestamp
                }
            },
            upsert=True
        )
    
    def get_user_objects(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve objects for a user with metadata.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary with objects, created_at, and updated_at (empty dict if none found)
        """
        doc = self.objects_collection.find_one({"user_id": user_id})
        
        if doc and "objects" in doc:
            return {
                "objects": doc["objects"],
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at")
            }
        return {
            "objects": [],
            "created_at": None,
            "updated_at": None
        }
    
    def delete_user_objects(self, user_id: str) -> None:
        """
        Delete all objects for a user.
        
        Args:
            user_id: The user ID
        """
        self.objects_collection.delete_one({"user_id": user_id})
    
    def close(self):
        """Close the MongoDB connection."""
        self.client.close()


# Global database instance
db = Database()
