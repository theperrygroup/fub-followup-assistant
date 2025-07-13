"""Simplified FastAPI application for FUB Follow-up Assistant.

This is a minimal version that bypasses SQLModel issues and uses direct database queries.
Railway deployment version.
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
        print(f"Database test failed: {e}")
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
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 