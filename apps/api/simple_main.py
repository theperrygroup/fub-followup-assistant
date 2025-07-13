"""Simplified FastAPI application for FUB Follow-up Assistant.

This is a minimal version that bypasses SQLModel issues and uses direct database queries.
Railway deployment version.
"""

import asyncio
import contextlib
from typing import Dict, Any

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

# Database connection pool
db_pool = None

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
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
    
    yield
    
    # Shutdown
    if db_pool:
        await db_pool.close()

# Create FastAPI application
app = FastAPI(
    title="FUB Follow-up Assistant API",
    description="AI-powered follow-up assistant for Follow Up Boss CRM",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

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

@app.post("/api/v1/setup-db")
async def setup_database() -> Dict[str, Any]:
    """Initialize database tables and indexes."""
    global db_pool
    
    if not db_pool:
        return {"error": "Database pool not initialized"}
    
    # Database initialization SQL
    init_sql = """
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Create accounts table
    CREATE TABLE IF NOT EXISTS accounts (
        account_id SERIAL PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        fub_access_token TEXT,
        fub_account_id VARCHAR(255) UNIQUE NOT NULL,
        fub_refresh_token TEXT,
        stripe_customer_id VARCHAR(255),
        subscription_status VARCHAR(50) DEFAULT 'trialing',
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create chat_messages table
    CREATE TABLE IF NOT EXISTS chat_messages (
        answer TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        person_id VARCHAR(255) NOT NULL,
        question TEXT NOT NULL,
        role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant'))
    );

    -- Create rate_limit_entries table
    CREATE TABLE IF NOT EXISTS rate_limit_entries (
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        id SERIAL PRIMARY KEY,
        identifier VARCHAR(255) NOT NULL,
        request_count INTEGER DEFAULT 1,
        window_start TIMESTAMP WITH TIME ZONE NOT NULL
    );

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_accounts_fub_account_id ON accounts(fub_account_id);
    CREATE INDEX IF NOT EXISTS idx_accounts_stripe_customer_id ON accounts(stripe_customer_id);
    CREATE INDEX IF NOT EXISTS idx_chat_messages_person_id ON chat_messages(person_id);
    CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
    CREATE INDEX IF NOT EXISTS idx_rate_limit_entries_identifier ON rate_limit_entries(identifier);
    CREATE INDEX IF NOT EXISTS idx_rate_limit_entries_window_start ON rate_limit_entries(window_start);

    -- Create function to update updated_at timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Create trigger for accounts table
    CREATE TRIGGER update_accounts_updated_at 
        BEFORE UPDATE ON accounts 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    """
    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(init_sql)
            
            # Verify tables were created
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            return {
                "status": "success",
                "message": "Database initialized successfully",
                "tables_created": [row["table_name"] for row in tables]
            }
    except Exception as e:
        print(f"Database setup failed: {e}")
        return {"error": str(e), "status": "failed"}


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