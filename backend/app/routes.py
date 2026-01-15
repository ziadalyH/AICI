"""
API routes for the Backend API.
"""
from fastapi import APIRouter, HTTPException, status, Depends
import httpx

from .models import (
    UserCreate, UserLogin, Token, AuthResponse, User,
    SessionObjectsRequest, SessionObjectsResponse,
    QueryRequest, QueryResponse
)
from .database import db
from .auth import create_access_token, authenticate_user, get_current_user
from .session import session_store
from .error_handler import log_error, log_warning, log_info


# Create router for authentication endpoints
auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Create router for session endpoints
session_router = APIRouter(prefix="/api/session", tags=["session"])


@auth_router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    
    Args:
        user_data: User registration data (username and password)
        
    Returns:
        AuthResponse with success status and message
        
    Raises:
        HTTPException: If username already exists or validation fails
    """
    try:
        # Create user in database
        user = db.create_user(user_data.username, user_data.password)
        
        log_info(
            info_type="USER_REGISTRATION",
            message=f"User '{user.username}' registered successfully",
            user_id=user.id
        )
        
        return AuthResponse(
            success=True,
            message=f"User '{user.username}' registered successfully"
        )
    except ValueError as e:
        log_warning(
            warning_type="REGISTRATION_FAILED",
            message=f"Registration failed for username '{user_data.username}': {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        log_error(
            error_type="REGISTRATION_ERROR",
            message="An error occurred during registration",
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )


@auth_router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Authenticate a user and return a JWT token.
    
    Args:
        credentials: User login credentials (username and password)
        
    Returns:
        Token object containing JWT access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Authenticate user
    user = authenticate_user(credentials.username, credentials.password)
    
    if not user:
        log_warning(
            warning_type="AUTHENTICATION_FAILED",
            message=f"Failed login attempt for username '{credentials.username}'"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create session for user
    session_store.create_session(user.id)
    
    # Load user's saved objects from database into session
    db_data = db.get_user_objects(user.id)
    saved_objects = db_data.get("objects", [])
    if saved_objects:
        session = session_store.get_session_by_user(user.id)
        if session:
            session_store.store_objects(session.session_id, saved_objects)
    
    # Generate JWT token
    access_token = create_access_token(user.id, user.username)
    
    log_info(
        info_type="USER_LOGIN",
        message=f"User '{user.username}' logged in successfully",
        user_id=user.id
    )
    
    return Token(token=access_token, token_type="bearer")


# Protected route example to test authentication
@auth_router.get("/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: The authenticated user (injected by dependency)
        
    Returns:
        Dictionary with user information
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "created_at": current_user.created_at.isoformat()
    }


# Session management endpoints
@session_router.post("/objects", response_model=SessionObjectsResponse)
async def upload_objects(
    request: SessionObjectsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Upload or update ephemeral objects for the current user's session.
    
    Args:
        request: Request containing list of objects
        current_user: The authenticated user (injected by dependency)
        
    Returns:
        SessionObjectsResponse with success status and session ID
        
    Raises:
        HTTPException: If session operations fail
    """
    try:
        # Get or create session for user
        session = session_store.get_session_by_user(current_user.id)
        
        if not session:
            # Create new session if none exists
            session_id = session_store.create_session(current_user.id)
        else:
            session_id = session.session_id
        
        # Store objects in session (for current session)
        session_store.store_objects(session_id, request.objects)
        
        # Save objects to database (for persistence)
        db.save_user_objects(current_user.id, request.objects)
        
        log_info(
            info_type="OBJECTS_UPDATED",
            message=f"Stored {len(request.objects)} objects in session and database",
            user_id=current_user.id,
            session_id=session_id
        )
        
        return SessionObjectsResponse(
            success=True,
            message=f"Stored {len(request.objects)} objects in session",
            session_id=session_id
        )
    except ValueError as e:
        log_error(
            error_type="SESSION_ERROR",
            message=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        log_error(
            error_type="SESSION_ERROR",
            message="An error occurred while storing objects",
            user_id=current_user.id,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while storing objects"
        )


@session_router.get("/objects", response_model=SessionObjectsResponse)
async def get_objects(current_user: User = Depends(get_current_user)):
    """
    Retrieve ephemeral objects from the current user's session.
    
    Args:
        current_user: The authenticated user (injected by dependency)
        
    Returns:
        SessionObjectsResponse with objects list and timestamps
        
    Raises:
        HTTPException: If session not found or operations fail
    """
    try:
        # Get session for user
        session = session_store.get_session_by_user(current_user.id)
        
        if not session:
            log_warning(
                warning_type="SESSION_NOT_FOUND",
                message="Session not found or expired",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )
        
        # Retrieve objects from session
        objects = session_store.get_objects(session.session_id)
        
        # Get metadata from database
        db_data = db.get_user_objects(current_user.id)
        
        return SessionObjectsResponse(
            success=True,
            objects=objects,
            session_id=session.session_id,
            created_at=db_data.get("created_at").isoformat() if db_data.get("created_at") else None,
            updated_at=db_data.get("updated_at").isoformat() if db_data.get("updated_at") else None
        )
    except ValueError as e:
        log_error(
            error_type="SESSION_ERROR",
            message=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            error_type="SESSION_ERROR",
            message="An error occurred while retrieving objects",
            user_id=current_user.id,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving objects"
        )


# Create router for query endpoints
query_router = APIRouter(prefix="/api", tags=["query"])


@query_router.post("/query")
async def process_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Process a user query using the AI Agent.
    
    This endpoint:
    1. Retrieves the user's session objects (drawing JSON)
    2. Sends the question and objects to the AI Agent
    3. Returns the AI-generated answer
    
    Args:
        request: QueryRequest containing the user's question
        current_user: The authenticated user (injected by dependency)
        
    Returns:
        QueryResponse with the AI-generated answer
        
    Raises:
        HTTPException: If session not found or AI Agent communication fails
    """
    from .ai_agent_client import ai_agent_client
    
    try:
        # Get session for user
        session = session_store.get_session_by_user(current_user.id)
        
        if not session:
            log_warning(
                warning_type="SESSION_NOT_FOUND",
                message="Session not found for query",
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found. Please login again."
            )
        
        # Retrieve objects from session (drawing JSON)
        objects = session_store.get_objects(session.session_id)
        
        log_info(
            info_type="QUERY_PROCESSING",
            message=f"Processing query with {len(objects)} objects",
            user_id=current_user.id,
            session_id=session.session_id
        )
        
        # Send query to AI Agent
        response = await ai_agent_client.query(
            question=request.question,
            objects=objects,
            top_k=getattr(request, 'top_k', 5)
        )
        
        log_info(
            info_type="QUERY_SUCCESS",
            message="Query processed successfully",
            user_id=current_user.id
        )
        
        # Return full response (answer, sources, answer_type, drawing_context_used)
        return QueryResponse(
            answer=response.get("answer", ""),
            sources=response.get("sources"),
            answer_type=response.get("answer_type", "no_answer"),
            drawing_context_used=response.get("drawing_context_used", False)
        )
        
    except ValueError as e:
        log_error(
            error_type="QUERY_VALIDATION_ERROR",
            message=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except httpx.TimeoutException as e:
        log_error(
            error_type="AI_AGENT_TIMEOUT",
            message="AI Agent request timed out",
            user_id=current_user.id,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI Agent request timed out. Please try again."
        )
    except httpx.ConnectError as e:
        log_error(
            error_type="AI_AGENT_CONNECTION_ERROR",
            message="Unable to connect to AI Agent",
            user_id=current_user.id,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Agent service is currently unavailable. Please try again later."
        )
    except httpx.HTTPStatusError as e:
        log_error(
            error_type="AI_AGENT_ERROR",
            message=f"AI Agent returned error: {e.response.status_code}",
            user_id=current_user.id,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI Agent returned an error. Please try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            error_type="QUERY_ERROR",
            message="An unexpected error occurred while processing query",
            user_id=current_user.id,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your query"
        )
