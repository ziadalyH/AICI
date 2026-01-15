"""
Hybrid RAG AI Agent Service - Integrated with Explaino RAG
Combines user's drawing JSON with PDF document retrieval for intelligent Q&A
"""
import os
import sys
import logging
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import Config
from src.rag_system import RAGSystem
from src.models import PDFResponse, NoAnswerResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    question: str = Field(..., description="User's natural-language question", min_length=1)
    drawing_json: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="User's drawing JSON from session (can be object or array of drawing elements)"
    )
    top_k: Optional[int] = Field(
        default=5,
        description="Number of document chunks to retrieve",
        ge=1,
        le=20
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the height restrictions for my building?",
                "drawing_json": [
                    {"type": "POLYLINE", "layer": "Walls", "points": [[0, 0], [10, 0], [10, 10], [0, 10]], "closed": True},
                    {"type": "POLYLINE", "layer": "Plot Boundary", "points": [[0, 0], [20, 0], [20, 20], [0, 20]], "closed": True}
                ],
                "top_k": 5
            }
        }


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    answer: str = Field(..., description="AI-generated answer combining documents and drawing context")
    answer_type: str = Field(..., description="Type of answer: video, pdf, or no_answer")
    sources: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Retrieved document sources"
    )
    drawing_context_used: bool = Field(
        default=False,
        description="Whether drawing JSON was used in reasoning"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on the regulations and your building specifications (height: 15.5m, 3 floors), your building exceeds the maximum height limit of 12m for residential zones.",
                "answer_type": "pdf",
                "sources": [
                    {
                        "document": "Building Regulations 2024",
                        "page": 5,
                        "relevance": 0.89
                    }
                ],
                "drawing_context_used": True
            }
        }


# Global RAG system instance
rag_system: Optional[RAGSystem] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes the RAG system on startup.
    """
    global rag_system
    
    # Startup: Initialize the RAG system
    try:
        logger.info("=" * 80)
        logger.info("Initializing Hybrid RAG AI Agent with Explaino")
        logger.info("=" * 80)
        
        # Load configuration from environment variables
        config = Config.from_env()
        
        # Initialize RAG system
        rag_system = RAGSystem(config)
        
        # Check if index exists
        if not rag_system.check_index_exists():
            logger.warning("⚠️  No vector index found. Please run indexing first:")
            logger.warning("   python -m src build-index")
        
        logger.info("✓ Hybrid RAG AI Agent initialized successfully")
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize Hybrid RAG AI Agent: {str(e)}")
        raise
    
    yield
    
    # Shutdown: Cleanup if needed
    rag_system = None
    logger.info("Hybrid RAG AI Agent shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Hybrid RAG AI Agent Service",
    description="Combines user's drawing JSON with PDF document retrieval for intelligent Q&A using Explaino RAG",
    version="2.0.0",
    lifespan=lifespan
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "service": "Hybrid RAG AI Agent",
        "status": "running",
        "version": "2.0.0",
        "features": [
            "Drawing JSON context integration",
            "PDF document retrieval",
            "Advanced query preprocessing",
            "Multi-source reasoning with Explaino RAG"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if rag_system is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hybrid RAG AI Agent not initialized"
        )
    
    # Check if index exists
    index_exists = rag_system.check_index_exists()
    
    return {
        "status": "healthy" if index_exists else "degraded",
        "pipeline_ready": True,
        "index_exists": index_exists
    }


@app.post("/api/agent/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query using the hybrid RAG pipeline with Explaino.
    
    This endpoint:
    1. Takes user's question and optional drawing JSON
    2. Preprocesses the question (stopword removal, etc.)
    3. Retrieves relevant PDF documents using Explaino RAG
    4. Combines retrieved documents with user's drawing JSON
    5. Sends both to LLM for reasoning
    6. Returns the best answer
    
    Args:
        request: QueryRequest containing question, drawing_json, and optional top_k
        
    Returns:
        QueryResponse with the generated answer and sources
        
    Raises:
        HTTPException: If pipeline is not initialized or query processing fails
    """
    # Check if pipeline is initialized
    if rag_system is None:
        logger.error("Query attempted but RAG system not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Agent service temporarily unavailable"
        )
    
    # Validate request
    if not request.question or not request.question.strip():
        logger.warning("Empty query submitted")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )
    
    try:
        logger.info(f"Processing query: {request.question}")
        logger.info(f"Drawing JSON provided: {bool(request.drawing_json)}")
        if request.drawing_json:
            logger.info(f"Drawing JSON type: {type(request.drawing_json)}")
            if isinstance(request.drawing_json, list):
                logger.info(f"Drawing JSON is a list with {len(request.drawing_json)} elements")
                logger.info(f"Drawing JSON preview: {str(request.drawing_json)[:500]}...")
            elif isinstance(request.drawing_json, dict):
                logger.info(f"Drawing JSON is a dict with keys: {list(request.drawing_json.keys())}")
                logger.info(f"Drawing JSON preview: {str(request.drawing_json)[:500]}...")
            else:
                logger.info(f"Drawing JSON content: {request.drawing_json}")
        
        # Process the query through the RAG system (with drawing JSON)
        result = rag_system.answer_question(
            question=request.question,
            drawing_json=request.drawing_json if request.drawing_json else None
        )
        
        # Extract answer and sources based on result type
        if isinstance(result, PDFResponse):
            answer = result.generated_answer
            answer_type = "pdf"
            
            # Use all_sources if available, otherwise create single source
            if result.all_sources:
                sources = result.all_sources
            else:
                # Single source (backward compatibility)
                source = {
                    "type": "pdf",
                    "document": result.pdf_filename,
                    "page": result.page_number,
                    "paragraph": result.paragraph_index,
                    "snippet": result.source_snippet,
                    "relevance": result.score,
                    "title": result.title,
                    "selected": True  # Single source is always selected
                }
                
                # For JSON-only responses, mark as drawing analysis
                if result.pdf_filename == "[Drawing Analysis]":
                    source["type"] = "drawing"
                    source["document"] = "Drawing Analysis"
                
                sources = [source]
            
            drawing_context_used = bool(request.drawing_json)
        elif isinstance(result, NoAnswerResponse):
            answer = result.message
            answer_type = "no_answer"
            sources = None
            drawing_context_used = False
        else:
            raise ValueError(f"Unexpected result type: {type(result)}")
        
        logger.info("Query processed successfully")
        
        # Return response
        return QueryResponse(
            answer=answer,
            answer_type=answer_type,
            sources=sources,
            drawing_context_used=drawing_context_used
        )
        
    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Query validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # Log the error with full details
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        
        # Check if it's an LLM API error
        error_msg = str(e).lower()
        if "api" in error_msg or "openai" in error_msg or "rate limit" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable"
            )
        
        # Return generic error for unexpected issues
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: An unexpected error occurred"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
