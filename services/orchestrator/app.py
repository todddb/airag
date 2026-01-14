"""
Orchestrator API - Main Application

This is the main entry point for the Orchestrator service.
Handles intent classification, query planning, and response validation.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# Local imports
from orchestrator import Orchestrator
from lib.streaming_handler import StreamingHandler

# =============================================================================
# Configuration
# =============================================================================

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger.add(
    "/app/logs/orchestrator.log",
    rotation="100 MB",
    retention="7 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
)

# Environment variables
ORCHESTRATOR_OLLAMA_URL = os.getenv("ORCHESTRATOR_OLLAMA_URL", "http://orchestrator-ollama:11434")
WORKER_API_URL = os.getenv("WORKER_API_URL", "http://worker-api:8001")
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "qwen2.5:14b")
STREAMING_ENABLED = os.getenv("STREAMING_ENABLED", "true").lower() == "true"

# =============================================================================
# Lifespan Management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Orchestrator API")
    logger.info(f"Orchestrator Ollama URL: {ORCHESTRATOR_OLLAMA_URL}")
    logger.info(f"Worker API URL: {WORKER_API_URL}")
    logger.info(f"Model: {ORCHESTRATOR_MODEL}")
    logger.info(f"Streaming: {STREAMING_ENABLED}")
    
    # Initialize orchestrator
    app.state.orchestrator = Orchestrator(
        ollama_url=ORCHESTRATOR_OLLAMA_URL,
        worker_api_url=WORKER_API_URL,
        model=ORCHESTRATOR_MODEL,
    )
    
    # Initialize streaming handler
    app.state.streaming_handler = StreamingHandler()
    
    # Verify Ollama connection
    try:
        await app.state.orchestrator.verify_connection()
        logger.info("✓ Orchestrator LLM connection verified")
    except Exception as e:
        logger.error(f"✗ Failed to connect to Orchestrator LLM: {e}")
        logger.warning("Service starting anyway - requests will fail until LLM is available")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Orchestrator API")

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="AI RAG Orchestrator API",
    description="Intent classification, query planning, and response validation service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Request/Response Models
# =============================================================================

class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str = Field(..., description="The user's question", min_length=1)
    session_id: Optional[str] = Field(None, description="Optional session ID for context")
    stream: bool = Field(True, description="Whether to stream the response")

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    orchestrator_model: str
    llm_available: bool

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    trace_id: Optional[str] = None

# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status and configuration
    """
    orchestrator = app.state.orchestrator
    
    # Check LLM availability
    llm_available = False
    try:
        await orchestrator.verify_connection()
        llm_available = True
    except Exception:
        pass
    
    return HealthResponse(
        status="healthy" if llm_available else "degraded",
        service="orchestrator",
        version="1.0.0",
        orchestrator_model=ORCHESTRATOR_MODEL,
        llm_available=llm_available,
    )

# =============================================================================
# Main Ask Endpoint
# =============================================================================

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Main endpoint for asking questions.
    
    This endpoint orchestrates the entire query process:
    1. Classify intent
    2. Plan query strategy
    3. Execute via worker
    4. Validate response
    5. Return or stream result
    
    Args:
        request: Question request with optional streaming
        
    Returns:
        Streaming response (SSE) or JSON response
    """
    orchestrator = app.state.orchestrator
    streaming_handler = app.state.streaming_handler
    
    logger.info(f"Received question: {request.question[:100]}...")
    
    try:
        if request.stream and STREAMING_ENABLED:
            # Stream the response with thinking process
            async def generate_stream():
                async for event in orchestrator.process_question_streaming(
                    question=request.question,
                    session_id=request.session_id,
                ):
                    yield event
            
            return EventSourceResponse(generate_stream())
        else:
            # Non-streaming response
            result = await orchestrator.process_question(
                question=request.question,
                session_id=request.session_id,
            )
            
            return JSONResponse(content=result)
            
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )

# =============================================================================
# Classification-Only Endpoint (for debugging)
# =============================================================================

@app.post("/classify")
async def classify_intent(request: QuestionRequest):
    """
    Classify user intent without executing the query.
    
    Useful for debugging and testing intent classification.
    
    Args:
        request: Question to classify
        
    Returns:
        Classification result with intent, confidence, and extracted parameters
    """
    orchestrator = app.state.orchestrator
    
    try:
        classification = await orchestrator.classify_intent(request.question)
        return JSONResponse(content=classification.model_dump())
    except Exception as e:
        logger.error(f"Error classifying intent: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error classifying intent: {str(e)}"
        )

# =============================================================================
# Validation-Only Endpoint (for debugging)
# =============================================================================

class ValidateRequest(BaseModel):
    """Request model for validation endpoint."""
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Answer to validate")
    citations: list = Field(default=[], description="Citations provided")

@app.post("/validate")
async def validate_response(request: ValidateRequest):
    """
    Validate a response without full orchestration.
    
    Useful for testing validation logic.
    
    Args:
        request: Validation request with question, answer, citations
        
    Returns:
        Validation result
    """
    orchestrator = app.state.orchestrator
    
    try:
        validation = await orchestrator.validate_response(
            question=request.question,
            answer=request.answer,
            citations=request.citations,
        )
        return JSONResponse(content=validation.model_dump())
    except Exception as e:
        logger.error(f"Error validating response: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error validating response: {str(e)}"
        )

# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc),
        ).model_dump(),
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
        ).model_dump(),
    )

# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "AI RAG Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "model": ORCHESTRATOR_MODEL,
        "endpoints": {
            "health": "/health",
            "ask": "/ask",
            "classify": "/classify",
            "validate": "/validate",
            "docs": "/docs",
        }
    }

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEV_MODE", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
