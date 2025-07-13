"""Main FastAPI application for FUB Follow-up Assistant.

This module sets up the FastAPI application with working database connectivity.
"""

import sys
import asyncio
from typing import Dict, Any

import asyncpg
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from config import settings


# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level=settings.log_level,
    serialize=True if settings.app_env == "prod" else False
)

# Database connection pool
db_pool = None

# Create FastAPI application
app = FastAPI(
    title="FUB Follow-up Assistant API",
    description="AI-powered follow-up assistant for Follow Up Boss CRM",
    version="1.0.0",
    docs_url="/docs" if settings.app_env != "prod" else None,
    redoc_url="/redoc" if settings.app_env != "prod" else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*.followupboss.com",
        settings.frontend_embed_origin,
        settings.marketing_origin
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database connection pool."""
    global db_pool
    logger.info("Starting FUB Follow-up Assistant API")
    
    # Parse the DATABASE_URL to extract connection parameters
    import urllib.parse as urlparse
    url = urlparse.urlparse(settings.database_url)
    
    try:
        db_pool = await asyncpg.create_pool(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path[1:],  # Remove leading '/'
            min_size=1,
            max_size=5
        )
        logger.info("✅ Database connection pool created")
    except Exception as e:
        logger.error(f"❌ Failed to create database pool: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Close database connection pool."""
    global db_pool
    if db_pool:
        await db_pool.close()
    logger.info("Shutting down FUB Follow-up Assistant API")


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    """Log incoming requests."""
    start_time = asyncio.get_event_loop().time()
    
    # Log request
    logger.info(f"🌐 {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
    
    # Process request
    try:
        response = await call_next(request)
        duration = asyncio.get_event_loop().time() - start_time
        logger.info(f"✅ {request.method} {request.url.path} -> {response.status_code} ({duration:.3f}s)")
        return response
    except Exception as e:
        duration = asyncio.get_event_loop().time() - start_time
        logger.error(f"❌ {request.method} {request.url.path} -> ERROR ({duration:.3f}s): {e}")
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception in {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error",
            "request_id": request.headers.get("x-request-id", "unknown")
        }
    )


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    global db_pool
    
    status = "healthy"
    db_status = "connected"
    
    # Test database connection
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            status = "unhealthy"
            db_status = "disconnected"
    else:
        status = "unhealthy"
        db_status = "no_pool"
    
    return {
        "status": status,
        "service": "fub-followup-assistant-api",
        "version": "1.0.0",
        "environment": settings.app_env,
        "database": db_status
    }


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "FUB Follow-up Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/v1/test-db")
async def test_database() -> Dict[str, Any]:
    """Test database connectivity and return sample data."""
    global db_pool
    
    if not db_pool:
        return {"error": "Database pool not initialized"}
    
    try:
        async with db_pool.acquire() as conn:
            # Test basic connectivity
            test_result = await conn.fetchval("SELECT 1 as test")
            
            # Get table info
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            # Get account count
            account_count = await conn.fetchval("SELECT COUNT(*) FROM accounts")
            
            return {
                "database_test": test_result,
                "tables": [row["table_name"] for row in tables],
                "account_count": account_count,
                "status": "connected"
            }
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return {"error": str(e), "status": "failed"}


# Basic authentication endpoints
@app.post("/api/v1/auth/iframe-login")
async def iframe_login() -> Dict[str, str]:
    """Placeholder iframe login endpoint."""
    return {
        "message": "Iframe login endpoint - implementation needed",
        "status": "placeholder"
    }


@app.post("/api/v1/fub/note")
async def create_fub_note() -> Dict[str, str]:
    """Placeholder FUB note creation endpoint."""
    return {
        "message": "FUB note creation endpoint - implementation needed", 
        "status": "placeholder"
    }


@app.post("/api/v1/chat/message")
async def chat_message() -> Dict[str, str]:
    """Placeholder chat message endpoint."""
    return {
        "message": "Chat message endpoint - implementation needed",
        "status": "placeholder"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "dev",
        log_config=None  # Use our custom logging
    ) 