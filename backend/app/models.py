"""
Data models for the Backend API.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class User(BaseModel):
    """User model for authentication."""
    id: str
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(BaseModel):
    """Request model for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Request model for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Response model for authentication token."""
    token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Response model for authentication operations."""
    success: bool
    message: Optional[str] = None
    token: Optional[str] = None


class SessionObjectsRequest(BaseModel):
    """Request model for uploading ephemeral objects."""
    objects: list[dict] = Field(..., description="List of ephemeral objects")


class SessionObjectsResponse(BaseModel):
    """Response model for session objects operations."""
    success: bool
    message: Optional[str] = None
    objects: Optional[list[dict]] = None
    session_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class QueryRequest(BaseModel):
    """Request model for query processing."""
    question: str = Field(..., min_length=1, description="User's natural-language question")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of document chunks to retrieve")


class QueryResponse(BaseModel):
    """Response model for query processing."""
    answer: str = Field(..., description="AI-generated answer to the question")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of source documents with citations")
    answer_type: str = Field(default="no_answer", description="Type of answer: pdf, drawing, or no_answer")
    drawing_context_used: bool = Field(default=False, description="Whether drawing JSON was used in the answer")
