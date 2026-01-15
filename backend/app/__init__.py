# Backend API Application

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import auth_router, session_router, query_router
from .error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="Hybrid RAG Q&A System - Backend API",
        description="Backend API for authentication and session management",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # Include routers
    app.include_router(auth_router)
    app.include_router(session_router)
    app.include_router(query_router)
    
    @app.get("/")
    async def root():
        return {"message": "Hybrid RAG Q&A System - Backend API"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return app


# Create application instance
app = create_app()
