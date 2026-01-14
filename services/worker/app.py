"""
Worker API - Main Application

This is the main entry point for the Worker service.
Executes RAG searches, structured lookups, and generates answers.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

# Local imports
from lib.rag_engine import RAGEngine
from lib.structured_lookup import StructuredLookup
from lib.context_builder import ContextBuilder
from lib.embeddings import EmbeddingGenerator

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
    "/app/logs/worker.log",
    rotation="100 MB",
    retention="7 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
)

# Environment variables
WORKER_OLLAMA_URL = os.getenv("WORKER_OLLAMA_URL", "http://worker-ollama:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
WORKER_MODEL = os.getenv("WORKER_MODEL", "qwen2.5:32b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")

# =============================================================================
# Lifespan Management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Worker API")
    logger.info(f"Worker Ollama URL: {WORKER_OLLAMA_URL}")
    logger.info(f"Qdrant URL: {QDRANT_URL}")
    logger.info(f"Model: {WORKER_MODEL}")
    logger.info(f"Embedding Model: {EMBEDDING_MODEL}")
    logger.info(f"Collection: {QDRANT_COLLECTION}")
    
    # Initialize Qdrant client
    app.state.qdrant_client = QdrantClient(url=QDRANT_URL)
    logger.info("✓ Qdrant client initialized")
    
    # Initialize embedding generator
    app.state.embedding_generator = EmbeddingGenerator(
        model_name=EMBEDDING_MODEL,
    )
    logger.info("✓ Embedding generator initialized")
    
    # Initialize context builder
    app.state.context_builder = ContextBuilder()
    logger.info("✓ Context builder initialized")
    
    # Initialize structured lookup
    app.state.structured_lookup = StructuredLookup(
        qdrant_client=app.state.qdrant_client,
        collection_name=QDRANT_COLLECTION,
    )
    logger.info("✓ Structured lookup initialized")
    
    # Initialize RAG engine
    app.state.rag_engine = RAGEngine(
        ollama_url=WORKER_OLLAMA_URL,
        qdrant_client=app.state.qdrant_client,
        embedding_generator=app.state.embedding_generator,
        context_builder=app.state.context_builder,
        model=WORKER_MODEL,
        collection_name=QDRANT_COLLECTION,
    )
    logger.info("✓ RAG engine initialized")
    
    # Verify connections
    try:
        await app.state.rag_engine.verify_connection()
        logger.info("✓ Worker LLM connection verified")
    except Exception as e:
        logger.error(f"✗ Failed to connect to Worker LLM: {e}")
        logger.warning("Service starting anyway - requests will fail until LLM is available")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Worker API")
    app.state.qdrant_client.close()

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="AI RAG Worker API",
    description="RAG execution, structured lookup, and answer generation service",
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

class ExecuteRequest(BaseModel):
    """Request model for task execution."""
    task_type: str = Field(..., description="Type of task: structured_lookup, rag_search, fuzzy_match")
    question: str = Field(..., description="The user's question")
    params: Dict[str, Any] = Field(default_factory=dict, description="Task-specific parameters")
    config: Dict[str, Any] = Field(default_factory=dict, description="Execution configuration")

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    worker_model: str
    embedding_model: str
    qdrant_available: bool
    llm_available: bool

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
    rag_engine = app.state.rag_engine
    
    # Check Qdrant
    qdrant_available = False
    try:
        app.state.qdrant_client.get_collections()
        qdrant_available = True
    except Exception:
        pass
    
    # Check LLM
    llm_available = False
    try:
        await rag_engine.verify_connection()
        llm_available = True
    except Exception:
        pass
    
    return HealthResponse(
        status="healthy" if (qdrant_available and llm_available) else "degraded",
        service="worker",
        version="1.0.0",
        worker_model=WORKER_MODEL,
        embedding_model=EMBEDDING_MODEL,
        qdrant_available=qdrant_available,
        llm_available=llm_available,
    )

# =============================================================================
# Main Execute Endpoint
# =============================================================================

@app.post("/execute")
async def execute_task(request: ExecuteRequest):
    """
    Main endpoint for executing tasks.
    
    Handles:
    - structured_lookup: Fuzzy matching in tables/databases
    - rag_search: Semantic search and answer generation
    - fuzzy_match: Entity normalization and matching
    
    Args:
        request: Task execution request
        
    Returns:
        Task result with answer and citations
    """
    logger.info(f"Executing {request.task_type}: {request.question[:100]}...")
    
    try:
        if request.task_type == "structured_lookup":
            # Structured data lookup with fuzzy matching
            result = await execute_structured_lookup(request)
        
        elif request.task_type == "rag_search":
            # RAG search and answer generation
            result = await execute_rag_search(request)
        
        elif request.task_type == "fuzzy_match":
            # Fuzzy entity matching
            result = await execute_fuzzy_match(request)
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task type: {request.task_type}"
            )
        
        return JSONResponse(content={
            "success": True,
            "result": result,
        })
        
    except Exception as e:
        logger.error(f"Error executing task: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
            }
        )

# =============================================================================
# Task Execution Functions
# =============================================================================

async def execute_structured_lookup(request: ExecuteRequest) -> Dict[str, Any]:
    """
    Execute structured data lookup with fuzzy matching.
    
    This is what solves your per diem problem!
    
    Args:
        request: Execution request with params
        
    Returns:
        Lookup result with data and citations
    """
    structured_lookup = app.state.structured_lookup
    
    # Extract parameters
    params = request.params
    
    # Perform fuzzy lookup
    result = await structured_lookup.lookup(
        entity_type=params.get("entity_type", "unknown"),
        params=params,
        question=request.question,
    )
    
    return result

async def execute_rag_search(request: ExecuteRequest) -> Dict[str, Any]:
    """
    Execute RAG search and answer generation.
    
    Args:
        request: Execution request with query
        
    Returns:
        Generated answer with citations
    """
    rag_engine = app.state.rag_engine
    
    # Extract configuration
    top_k = request.params.get("top_k", 8)
    
    # Execute RAG
    result = await rag_engine.search_and_generate(
        query=request.question,
        top_k=top_k,
    )
    
    return result

async def execute_fuzzy_match(request: ExecuteRequest) -> Dict[str, Any]:
    """
    Execute fuzzy entity matching.
    
    Args:
        request: Execution request with entity
        
    Returns:
        Matched entity with confidence
    """
    structured_lookup = app.state.structured_lookup
    
    # Extract entity
    entity = request.params.get("entity", "")
    entity_type = request.params.get("entity_type", "location")
    
    # Perform fuzzy match
    result = await structured_lookup.fuzzy_match(
        entity=entity,
        entity_type=entity_type,
    )
    
    return result

# =============================================================================
# Direct Endpoints (for testing)
# =============================================================================

@app.post("/rag_search")
async def rag_search(
    query: str = Field(..., description="Search query"),
    top_k: int = Field(8, description="Number of results"),
):
    """
    Direct RAG search endpoint (for testing).
    
    Args:
        query: Search query
        top_k: Number of results
        
    Returns:
        Search results with generated answer
    """
    rag_engine = app.state.rag_engine
    
    try:
        result = await rag_engine.search_and_generate(
            query=query,
            top_k=top_k,
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in RAG search: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error in RAG search: {str(e)}"
        )

@app.post("/structured_lookup")
async def structured_lookup_direct(
    entity_type: str = Field(..., description="Type of entity"),
    entity: str = Field(..., description="Entity to look up"),
):
    """
    Direct structured lookup endpoint (for testing).
    
    Args:
        entity_type: Type of entity (location_rate, etc.)
        entity: Entity value
        
    Returns:
        Lookup result
    """
    structured_lookup = app.state.structured_lookup
    
    try:
        result = await structured_lookup.lookup(
            entity_type=entity_type,
            params={"entity": entity},
            question=f"Lookup {entity}",
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error in structured lookup: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error in structured lookup: {str(e)}"
        )

# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "AI RAG Worker",
        "version": "1.0.0",
        "status": "running",
        "model": WORKER_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "endpoints": {
            "health": "/health",
            "execute": "/execute",
            "rag_search": "/rag_search",
            "structured_lookup": "/structured_lookup",
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
        port=8001,
        reload=os.getenv("DEV_MODE", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
