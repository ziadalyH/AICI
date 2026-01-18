# Backend API

FastAPI backend service handling authentication, session management, and coordination between frontend and AI Agent.

## Features

- **JWT Authentication** - Secure user authentication with bcrypt password hashing
- **Session Management** - User session tracking with MongoDB storage
- **Drawing Storage** - Persistent storage of user's building drawings
- **Query Routing** - Routes queries to AI Agent (standard or agentic mode)
- **Auto Logout** - Automatic logout on JWT token expiration

## Quick Start (Docker - Recommended)

The Backend is part of the full system. See the main [README](../README.md) for complete setup.

```bash
# From project root
cd AICI
docker-compose up -d backend
```

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export SECRET_KEY=your-secret-key-change-in-production
export MONGODB_URL=mongodb://localhost:27017/
export MONGODB_DB_NAME=hybrid_rag_qa
export AI_AGENT_URL=http://localhost:8001
```

### 3. Start MongoDB

```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  mongo:7.0
```

### 4. Start the Backend

```bash
python main.py
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

## Configuration

Environment variables:

- `SECRET_KEY` - JWT secret key (required, change in production)
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration (default: 30)
- `MONGODB_URL` - MongoDB connection URL (default: mongodb://mongodb:27017/)
- `MONGODB_DB_NAME` - Database name (default: hybrid_rag_qa)
- `AI_AGENT_URL` - AI Agent service URL (default: http://ai-agent:8001)

## Security Notes

⚠️ **Important for Production:**

- Change `SECRET_KEY` to a secure random value
- Store secrets in environment variables
- Configure CORS origins properly (currently allows all)
- Use HTTPS in production
- Consider rate limiting for authentication endpoints
- Implement token refresh mechanism

## Dependencies

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **python-jose** - JWT token handling
- **passlib** - Password hashing with bcrypt
- **pymongo** - MongoDB driver
- **httpx** - HTTP client for AI Agent communication
- **pydantic** - Data validation
