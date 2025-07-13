"""Simplified FastAPI application for FUB Follow-up Assistant.

This is a minimal version that bypasses SQLModel issues and uses direct database queries.
Railway deployment version.
"""

import asyncio
import hashlib
import hmac
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import asyncpg
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from loguru import logger
from pydantic import BaseModel, Field

from config import settings


# Auth utility functions
def verify_hmac_signature(context: str, signature: str) -> bool:
    """Verify HMAC signature from Follow Up Boss iframe."""
    try:
        expected_signature = hmac.new(
            settings.fub_embed_secret.encode(),
            context.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"HMAC verification error: {e}")
        return False


def create_jwt_token(account_id: int, fub_account_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token for the authenticated user."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode = {
        "account_id": account_id,
        "fub_account_id": fub_account_id,
        "exp": expire
    }
    
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except JWTError as e:
        logger.error(f"JWT verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# Request/Response models
class IframeLoginRequest(BaseModel):
    """Request model for iframe login."""
    context: str = Field(..., description="Context data from FUB iframe")
    signature: str = Field(..., description="HMAC signature")


class IframeLoginResponse(BaseModel):
    """Response model for iframe login."""
    account_id: int = Field(..., description="Internal account ID")
    fub_account_id: str = Field(..., description="Follow Up Boss account ID")
    subscription_status: str = Field(..., description="Subscription status")
    token: str = Field(..., description="JWT token")

# Database helper functions
async def get_account_by_fub_id(fub_account_id: str) -> Optional[Dict[str, Any]]:
    """Get account by FUB account ID."""
    global db_pool
    
    if not db_pool:
        return None
    
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT account_id, fub_account_id, subscription_status, created_at, updated_at "
                "FROM accounts WHERE fub_account_id = $1",
                fub_account_id
            )
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting account by FUB ID {fub_account_id}: {e}")
        return None


async def create_or_update_account(fub_account_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Create or update account in database."""
    global db_pool
    
    if not db_pool:
        return None
    
    try:
        async with db_pool.acquire() as conn:
            # Try to get existing account
            existing = await conn.fetchrow(
                "SELECT account_id, fub_account_id, subscription_status FROM accounts WHERE fub_account_id = $1",
                fub_account_id
            )
            
            if existing:
                # Update existing account
                row = await conn.fetchrow(
                    """UPDATE accounts 
                       SET updated_at = CURRENT_TIMESTAMP
                       WHERE fub_account_id = $1 
                       RETURNING account_id, fub_account_id, subscription_status""",
                    fub_account_id
                )
            else:
                # Create new account
                subscription_status = kwargs.get('subscription_status', 'trialing')
                row = await conn.fetchrow(
                    """INSERT INTO accounts (fub_account_id, subscription_status) 
                       VALUES ($1, $2) 
                       RETURNING account_id, fub_account_id, subscription_status""",
                    fub_account_id, subscription_status
                )
            
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error creating/updating account {fub_account_id}: {e}")
        return None


# Database connection pool
db_pool = None

@asynccontextmanager
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
@app.post("/api/v1/auth/iframe-login", response_model=IframeLoginResponse)
async def iframe_login(request: IframeLoginRequest) -> IframeLoginResponse:
    """Authenticate iframe request and issue JWT token."""
    try:
        # Verify HMAC signature
        if not verify_hmac_signature(request.context, request.signature):
            logger.warning(f"Invalid HMAC signature for context: {request.context[:100]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        # Parse context data
        try:
            # Decode base64 context first, then parse JSON
            import base64
            import binascii
            decoded_context = base64.b64decode(request.context).decode('utf-8')
            context_data = json.loads(decoded_context)
        except (json.JSONDecodeError, binascii.Error, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse context data: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid context data"
            )
        
        account_data = context_data.get("account", {})
        fub_account_id = str(account_data.get("id"))
        
        if not fub_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing account ID in context"
            )
        
        # Create or get account
        account = await create_or_update_account(
            fub_account_id=fub_account_id,
            domain=account_data.get("domain", ""),
            owner_name=account_data.get("owner", {}).get("name", ""),
            owner_email=account_data.get("owner", {}).get("email", "")
        )
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account"
            )
        
        # Create JWT token
        token = create_jwt_token(
            account_id=account["account_id"],
            fub_account_id=fub_account_id
        )
        
        return IframeLoginResponse(
            account_id=account["account_id"],
            fub_account_id=fub_account_id,
            subscription_status=account["subscription_status"],
            token=token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Iframe login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@app.post("/auth/fub/callback", response_model=IframeLoginResponse)
async def fub_callback(request: IframeLoginRequest) -> IframeLoginResponse:
    """FUB callback endpoint - alias to iframe_login for FUB compatibility."""
    return await iframe_login(request)


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