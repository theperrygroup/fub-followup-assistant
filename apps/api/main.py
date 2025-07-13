"""Main FastAPI application for FUB Follow-up Assistant.

This module sets up the FastAPI application with all routes, middleware,
CORS configuration, and database initialization.
"""

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from sqlmodel import SQLModel, create_engine

from config import settings
from routes import auth, chat, fub, stripe_webhook


# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level=settings.log_level,
    serialize=True if settings.app_env == "prod" else False
)


# Database engine
engine = create_engine(settings.database_url)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    
    Args:
        app: FastAPI application instance.
        
    Yields:
        None during application runtime.
    """
    # Startup
    logger.info("Starting FUB Follow-up Assistant API")
    
    # Database tables are already created via init.sql, so skip auto-creation
    # SQLModel.metadata.create_all(engine)
    logger.info("Using existing database schema")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FUB Follow-up Assistant API")


# Create FastAPI application
app = FastAPI(
    title="FUB Follow-up Assistant API",
    description="AI-powered follow-up assistant for Follow Up Boss CRM",
    version="1.0.0",
    lifespan=lifespan,
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


# Content Security Policy middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    """Add security headers to all responses.
    
    Args:
        request: FastAPI request object.
        call_next: Next middleware in chain.
        
    Returns:
        Response with security headers.
    """
    response = await call_next(request)
    
    # Content Security Policy for iframe embedding
    response.headers["Content-Security-Policy"] = "frame-ancestors *.followupboss.com"
    
    # Other security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    """Log all incoming requests.
    
    Args:
        request: FastAPI request object.
        call_next: Next middleware in chain.
        
    Returns:
        Response after processing.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info(
        f"Request: {request.method} {request.url.path} from {client_ip}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )
    
    response = await call_next(request)
    
    logger.info(
        f"Response: {response.status_code} for {request.method} {request.url.path}",
        extra={
            "status_code": response.status_code,
            "method": request.method,
            "path": request.url.path
        }
    )
    
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors.
    
    Args:
        request: FastAPI request object.
        exc: Exception that occurred.
        
    Returns:
        JSON error response.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_id": f"error_{id(exc)}"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.
    
    Returns:
        Health status information.
    """
    return {
        "status": "healthy",
        "service": "fub-followup-assistant-api",
        "version": "1.0.0",
        "environment": settings.app_env
    }


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(fub.router, prefix="/api/v1")
app.include_router(stripe_webhook.router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint.
    
    Returns:
        API information.
    """
    return {
        "message": "FUB Follow-up Assistant API",
        "version": "1.0.0",
        "docs": "/docs" if settings.app_env != "prod" else "Documentation disabled in production"
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