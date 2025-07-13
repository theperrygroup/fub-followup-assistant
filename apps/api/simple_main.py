"""Simplified FastAPI application for FUB Follow-up Assistant.

This is a minimal version that bypasses SQLModel issues and uses direct database queries.
"""

import asyncio
from typing import Dict, Any

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

# Create FastAPI application
app = FastAPI(
    title="FUB Follow-up Assistant API",
    description="AI-powered follow-up assistant for Follow Up Boss CRM",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Database connection pool
db_pool = None

@app.on_event("startup")
async def startup():
    """Initialize database connection pool."""
    global db_pool
    # Parse the DATABASE_URL to extract connection parameters
    import urllib.parse as urlparse
    url = urlparse.urlparse(settings.database_url)
    
    db_pool = await asyncpg.create_pool(
        host=url.hostname,
        port=url.port,
        user=url.username,
        password=url.password,
        database=url.path[1:],  # Remove leading '/'
        min_size=1,
        max_size=5
    )
    print("✅ Database connection pool created")

@app.on_event("shutdown")
async def shutdown():
    """Close database connection pool."""
    global db_pool
    if db_pool:
        await db_pool.close()

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    try:
        # Test database connection
        if db_pool is None:
            raise Exception("Database pool not initialized")
        async with db_pool.acquire() as conn:
            await conn.fetchval('SELECT 1')
        
        return {
            "status": "healthy",
            "service": "fub-followup-assistant-api",
            "version": "1.0.0",
            "environment": settings.app_env,
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "fub-followup-assistant-api",
            "version": "1.0.0",
            "environment": settings.app_env,
            "database": f"error: {str(e)}"
        }

# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "FUB Follow-up Assistant API",
        "version": "1.0.0",
        "status": "running"
    }

# Test database endpoint
@app.get("/api/v1/test-db")
async def test_database() -> Dict[str, Any]:
    """Test database connectivity and show sample data."""
    try:
        if db_pool is None:
            raise Exception("Database pool not initialized")
        async with db_pool.acquire() as conn:
            # Get database version
            version = await conn.fetchval('SELECT version()')
            
            # Get accounts count
            account_count = await conn.fetchval('SELECT COUNT(*) FROM accounts')
            
            # Get a sample account (safely)
            sample_account = await conn.fetchrow(
                'SELECT account_id, fub_account_id, subscription_status FROM accounts LIMIT 1'
            )
            
            return {
                "database_version": version,
                "accounts_count": account_count,
                "sample_account": dict(sample_account) if sample_account else None,
                "tables": ["accounts", "chat_messages", "rate_limit_entries"]
            }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 