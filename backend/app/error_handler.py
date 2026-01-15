"""
Error handling utilities for the Backend API.
Provides consistent error response formatting and logging.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standard error response format."""
    
    @staticmethod
    def format_error(
        code: str,
        message: str,
        details: Optional[str] = None,
        status_code: int = 500
    ) -> Dict[str, Any]:
        """
        Format an error response according to the design specification.
        
        Args:
            code: Error code identifier
            message: Human-readable error message
            details: Additional context (optional)
            status_code: HTTP status code
            
        Returns:
            Dictionary containing formatted error response
        """
        error_response = {
            "error": {
                "code": code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        if details:
            error_response["error"]["details"] = details
        
        return error_response


def log_error(
    error_type: str,
    message: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    exception: Optional[Exception] = None
):
    """
    Log an error with structured information.
    
    Args:
        error_type: Type of error (e.g., "AUTHENTICATION_ERROR", "QUERY_ERROR")
        message: Error message
        user_id: User ID if authenticated
        session_id: Session ID if applicable
        request_id: Request ID for tracing
        exception: Exception object if available
    """
    log_data = {
        "error_type": error_type,
        "error_message": message,  # Changed from "message" to avoid conflict
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if session_id:
        log_data["session_id"] = session_id
    if request_id:
        log_data["request_id"] = request_id
    
    if exception:
        logger.error(f"{error_type}: {message}", exc_info=exception, extra=log_data)
    else:
        logger.error(f"{error_type}: {message}", extra=log_data)


def log_warning(
    warning_type: str,
    message: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None
):
    """
    Log a warning with structured information.
    
    Args:
        warning_type: Type of warning
        message: Warning message
        user_id: User ID if authenticated
        session_id: Session ID if applicable
        request_id: Request ID for tracing
    """
    log_data = {
        "warning_type": warning_type,
        "warning_message": message,  # Changed from "message" to avoid conflict
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if session_id:
        log_data["session_id"] = session_id
    if request_id:
        log_data["request_id"] = request_id
    
    logger.warning(f"{warning_type}: {message}", extra=log_data)


def log_info(
    info_type: str,
    message: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """
    Log an info message with structured information.
    
    Args:
        info_type: Type of info message
        message: Info message
        user_id: User ID if authenticated
        session_id: Session ID if applicable
    """
    log_data = {
        "info_type": info_type,
        "info_message": message,  # Changed from "message" to avoid conflict
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if session_id:
        log_data["session_id"] = session_id
    
    logger.info(f"{info_type}: {message}", extra=log_data)


# Exception handlers for FastAPI

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions and return formatted error responses.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse with formatted error
    """
    # Map status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        410: "GONE",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
        507: "INSUFFICIENT_STORAGE"
    }
    
    error_code = error_code_map.get(exc.status_code, "ERROR")
    
    # Log the error
    log_error(
        error_type=error_code,
        message=str(exc.detail),
        request_id=request.headers.get("X-Request-ID")
    )
    
    # Return formatted error response
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.format_error(
            code=error_code,
            message=str(exc.detail),
            status_code=exc.status_code
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors.
    
    Args:
        request: FastAPI request object
        exc: Validation error
        
    Returns:
        JSONResponse with formatted error
    """
    # Extract validation error details
    errors = exc.errors()
    error_details = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in errors])
    
    # Log the validation error
    log_warning(
        warning_type="VALIDATION_ERROR",
        message=f"Request validation failed: {error_details}",
        request_id=request.headers.get("X-Request-ID")
    )
    
    # Return formatted error response
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse.format_error(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=error_details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception
        
    Returns:
        JSONResponse with formatted error
    """
    # Log the unexpected error with full stack trace
    log_error(
        error_type="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        request_id=request.headers.get("X-Request-ID"),
        exception=exc
    )
    
    # Return generic error response (don't expose internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.format_error(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    )
