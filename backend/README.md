# Backend API - Hybrid RAG Q&A System

## Overview

This is the Backend API component of the Hybrid RAG Q&A System. It handles user authentication, session management, and coordination between the frontend and AI Agent service.

## Implemented Features

### Task 2: Authentication System ✓

The following sub-tasks have been completed:

#### 2.1 User Model and Database Schema ✓

- **User model** with id, username, password_hash, and created_at fields
- **SQLite database** for persistent user storage
- **Password hashing** using bcrypt for secure password storage
- Database initialization and connection management

**Files:**

- `app/models.py` - Pydantic models for User, UserCreate, UserLogin, Token, AuthResponse
- `app/database.py` - Database class with user CRUD operations and password hashing

#### 2.3 JWT Token Generation and Validation ✓

- **Token generation** with configurable expiration (default: 24 hours)
- **Token validation** and decoding with error handling
- **Middleware** for protected routes using FastAPI dependencies
- User authentication with username/password verification

**Files:**

- `app/auth.py` - JWT token functions and authentication middleware

#### 2.5 Authentication API Endpoints ✓

- **POST /api/auth/register** - User registration endpoint
- **POST /api/auth/login** - User login endpoint returning JWT token
- **GET /api/auth/me** - Protected endpoint to get current user info
- Request/response models with validation

**Files:**

- `app/routes.py` - FastAPI router with authentication endpoints
- `app/__init__.py` - Main FastAPI application with CORS configuration

## Project Structure

```
backend/
├── app/
│   ├── __init__.py      # FastAPI application setup
│   ├── models.py        # Pydantic data models
│   ├── database.py      # SQLite database management
│   ├── auth.py          # JWT authentication logic
│   └── routes.py        # API endpoints
├── tests/
│   └── __init__.py
├── requirements.txt     # Python dependencies
├── main.py             # Server entry point
└── users.db            # SQLite database (created at runtime)
```

## Installation

1. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

## Running the Server

```bash
cd backend
python3 main.py
```

The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Health Check

- **GET /** - Root endpoint
- **GET /health** - Health check endpoint

### Authentication

- **POST /api/auth/register** - Register a new user

  - Request: `{"username": "string", "password": "string"}`
  - Response: `{"success": true, "message": "User registered successfully"}`

- **POST /api/auth/login** - Login and get JWT token

  - Request: `{"username": "string", "password": "string"}`
  - Response: `{"token": "jwt_token", "token_type": "bearer"}`

- **GET /api/auth/me** - Get current user info (protected)
  - Headers: `Authorization: Bearer <token>`
  - Response: `{"id": "uuid", "username": "string", "created_at": "iso_datetime"}`

## Testing

Manual tests have been created to verify functionality:

```bash
# Test authentication logic
python3 test_auth_manual.py

# Test API endpoints
python3 test_api_endpoints.py
```

## Requirements Validated

This implementation validates the following requirements:

- **Requirement 1.1**: User authentication with JWT token issuance ✓
- **Requirement 1.2**: Invalid credential rejection ✓
- **Requirement 1.3**: User registration ✓
- **Requirement 1.4**: JWT token authorization for authenticated requests ✓
- **Requirement 1.5**: Invalid/expired token rejection ✓

## Security Notes

⚠️ **Important for Production:**

- Change the `SECRET_KEY` in `app/auth.py` to a secure random value
- Store secrets in environment variables, not in code
- Configure CORS origins properly (currently set to allow all origins)
- Use HTTPS in production
- Consider adding rate limiting for authentication endpoints
- Implement token refresh mechanism for better security

## Next Steps

The following tasks are pending:

- Task 2.2: Write property test for user registration (optional)
- Task 2.4: Write property tests for authentication (optional)
- Task 2.6: Write property test for invalid credential rejection (optional)
- Task 3: Implement session management
- Task 8: Implement Backend-to-AI-Agent communication

## Dependencies

- **FastAPI**: Web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **python-jose**: JWT token encoding/decoding
- **passlib**: Password hashing with bcrypt
- **pydantic**: Data validation and settings management
- **SQLite**: Embedded database for user storage
- **pytest**: Testing framework
- **hypothesis**: Property-based testing framework
