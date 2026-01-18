"""
AI Agent client for Backend API.
Handles communication with the AI Agent service.
"""
import os
from typing import List, Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError


class AIAgentClient:
    """Client for communicating with the AI Agent service."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize the AI Agent client.
        
        Args:
            base_url: Base URL of the AI Agent service (defaults to env var or localhost)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url or os.getenv("AI_AGENT_URL", "http://localhost:8001")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Remove trailing slash from base URL
        self.base_url = self.base_url.rstrip("/")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
    )
    async def _make_request(
        self,
        question: str,
        objects: List[Dict[str, Any]],
        drawing_updated_at: Optional[str],
        top_k: int,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Internal method to make the HTTP request with retry logic.
        
        Args:
            question: User's natural-language question
            objects: List of ephemeral objects for the current session
            drawing_updated_at: ISO timestamp of when drawing was last updated
            top_k: Number of document chunks to retrieve
            session_id: Optional session ID for conversation history
            
        Returns:
            Full response dictionary with answer, sources, answer_type, etc.
            
        Raises:
            httpx.HTTPStatusError: If the AI Agent returns an error status
            httpx.TimeoutException: If the request times out
            httpx.ConnectError: If unable to connect to the AI Agent
        """
        # Prepare request payload
        payload = {
            "question": question,
            "drawing_json": objects,  # AI agent expects 'drawing_json' not 'objects'
            "drawing_updated_at": drawing_updated_at,
            "top_k": top_k
        }
        
        # Add session_id if provided
        if session_id:
            payload["session_id"] = session_id
        
        # Log the payload being sent
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Sending to AI Agent: question='{question[:50]}...', drawing_json={len(objects)} objects, drawing_updated_at={drawing_updated_at}, top_k={top_k}, session_id={session_id}")
        if objects:
            logger.info(f"Drawing JSON preview: {str(objects)[:200]}...")
        
        # Make async HTTP request to AI Agent
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/agent/query",
                json=payload
            )
            
            # Raise exception for error status codes
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return data  # Return full response, not just answer
    
    async def query(
        self,
        question: str,
        objects: List[Dict[str, Any]],
        drawing_updated_at: Optional[str] = None,
        top_k: int = 5,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a query to the AI Agent service.
        
        Args:
            question: User's natural-language question
            objects: List of ephemeral objects for the current session
            drawing_updated_at: ISO timestamp of when drawing was last updated
            top_k: Number of document chunks to retrieve (default: 5)
            session_id: Optional session ID for conversation history
            
        Returns:
            Full response dictionary with answer, sources, answer_type, etc.
            
        Raises:
            httpx.HTTPStatusError: If the AI Agent returns an error status
            httpx.TimeoutException: If the request times out
            httpx.ConnectError: If unable to connect to the AI Agent
            Exception: For other unexpected errors
        """
        # Validate inputs
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        try:
            return await self._make_request(question, objects, drawing_updated_at, top_k, session_id)
        
        except RetryError as e:
            # Extract the underlying exception from RetryError
            if e.last_attempt and e.last_attempt.exception():
                original_exception = e.last_attempt.exception()
                
                if isinstance(original_exception, httpx.TimeoutException):
                    raise httpx.TimeoutException(
                        f"AI Agent request timed out after {self.timeout} seconds"
                    ) from original_exception
                
                elif isinstance(original_exception, httpx.ConnectError):
                    raise httpx.ConnectError(
                        f"Unable to connect to AI Agent at {self.base_url}"
                    ) from original_exception
            
            # If we can't extract the original exception, raise a generic error
            raise httpx.ConnectError(
                f"Failed to connect to AI Agent after {self.max_retries} attempts"
            ) from e
        
        except httpx.HTTPStatusError as e:
            # Extract error details from response if available
            try:
                error_detail = e.response.json().get("detail", str(e))
            except Exception:
                error_detail = str(e)
            
            raise httpx.HTTPStatusError(
                message=f"AI Agent returned error: {error_detail}",
                request=e.request,
                response=e.response
            ) from e
    
    async def query_agentic(
        self,
        question: str,
        objects: List[Dict[str, Any]],
        drawing_updated_at: Optional[str] = None,
        top_k: int = 5,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a query to the AI Agent service using AGENTIC mode (multi-step reasoning).
        
        Args:
            question: User's natural-language question
            objects: List of ephemeral objects for the current session
            drawing_updated_at: ISO timestamp of when drawing was last updated
            top_k: Number of document chunks to retrieve (default: 5)
            session_id: Optional session ID for conversation history
            
        Returns:
            Full response dictionary with answer, sources, answer_type, reasoning_steps, etc.
            
        Raises:
            httpx.HTTPStatusError: If the AI Agent returns an error status
            httpx.TimeoutException: If the request times out
            httpx.ConnectError: If unable to connect to the AI Agent
            Exception: For other unexpected errors
        """
        # Validate inputs
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        # Prepare request payload
        payload = {
            "question": question,
            "drawing_json": objects,
            "drawing_updated_at": drawing_updated_at,
            "top_k": top_k
        }
        
        # Add session_id if provided
        if session_id:
            payload["session_id"] = session_id
        
        # Log the payload being sent
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🤖 Sending to AI Agent (AGENTIC MODE): question='{question[:50]}...', drawing_json={len(objects)} objects, session_id={session_id}")
        
        try:
            # Make async HTTP request to AI Agent's agentic endpoint
            async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for agentic mode
                response = await client.post(
                    f"{self.base_url}/api/agent/query-agentic",
                    json=payload
                )
                
                # Raise exception for error status codes
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                logger.info(f"✅ Agentic query completed with {len(data.get('reasoning_steps', []))} reasoning steps")
                return data
                
        except httpx.TimeoutException as e:
            raise httpx.TimeoutException(
                f"AI Agent agentic request timed out after 60 seconds"
            ) from e
        
        except httpx.ConnectError as e:
            raise httpx.ConnectError(
                f"Unable to connect to AI Agent at {self.base_url}"
            ) from e
        
        except httpx.HTTPStatusError as e:
            # Extract error details from response if available
            try:
                error_detail = e.response.json().get("detail", str(e))
            except Exception:
                error_detail = str(e)
            
            raise httpx.HTTPStatusError(
                message=f"AI Agent returned error: {error_detail}",
                request=e.request,
                response=e.response
            ) from e
    
    async def health_check(self) -> bool:
        """
        Check if the AI Agent service is healthy.
        
        Returns:
            True if the service is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_knowledge_summary(self) -> Dict[str, Any]:
        """
        Get the knowledge summary from the AI Agent.
        
        Returns:
            Dictionary with overview, topics, and suggested_questions
            
        Raises:
            httpx.HTTPStatusError: If the AI Agent returns an error status
            httpx.TimeoutException: If the request times out
            httpx.ConnectError: If unable to connect to the AI Agent
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/agent/knowledge-summary"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get knowledge summary: {e}")
            raise


# Global AI Agent client instance
ai_agent_client = AIAgentClient()
