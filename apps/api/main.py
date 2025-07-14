"""FastAPI application for FUB Follow-up Assistant.

This module contains all the functionality in a single file for simplicity.
"""

import os
import json
import hmac
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import asyncpg
from jose import jwt
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field


# Auth utility functions
def verify_hmac_signature(context: str, signature: str) -> bool:
    """Verify HMAC signature from Follow Up Boss iframe."""
    try:
        # Use the correct secret key for this app - fallback to hardcoded value if env var not set
        secret_key = os.environ.get('FUB_EMBED_SECRET', 'bbf8210af8db10b5a78ae3f01a4e61fc')
        
        logger.info("=== HMAC VERIFICATION START ===")
        logger.info(f"Secret key (first 10 chars): {secret_key[:10]}...")
        logger.info(f"Context length: {len(context)}")
        logger.info(f"Context (first 100 chars): {context[:100]}")
        logger.info(f"Context (last 100 chars): {context[-100:] if len(context) > 100 else 'N/A - context too short'}")
        logger.info(f"Provided signature: {signature}")
        logger.info(f"Signature length: {len(signature)}")
        
        expected_signature = hmac.new(
            secret_key.encode(),
            context.encode(),
            hashlib.sha256
        ).hexdigest()
        
        logger.info(f"Expected signature: {expected_signature}")
        logger.info(f"Signatures match: {hmac.compare_digest(signature, expected_signature)}")
        logger.info("=== HMAC VERIFICATION END ===")
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"HMAC verification error: {e}")
        return False


def create_jwt_token(account_id: int, fub_account_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token for authenticated user."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    payload = {
        "account_id": account_id,
        "fub_account_id": fub_account_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    secret_key = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt-secret-key-for-development')
    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_jwt_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        secret_key = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt-secret-key-for-development')
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


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


async def get_account_by_fub_id(fub_account_id: str) -> Optional[Dict[str, Any]]:
    """Get account by FUB account ID."""
    try:
        query = """
        SELECT account_id, fub_account_id, subscription_status, created_at, updated_at
        FROM accounts 
        WHERE fub_account_id = $1
        """
        
        result = await db_pool.fetchrow(query, fub_account_id)
        if result:
            return dict(result)
        return None
        
    except Exception as e:
        logger.error(f"Error getting account {fub_account_id}: {e}")
        return None


async def create_or_update_account(fub_account_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Create or update account record."""
    try:
        # Check if account exists
        existing = await get_account_by_fub_id(fub_account_id)
        
        if existing:
            logger.info(f"Account {fub_account_id} already exists, updating...")
            
            # Update existing account
            update_query = """
            UPDATE accounts 
            SET updated_at = CURRENT_TIMESTAMP
            WHERE fub_account_id = $1
            RETURNING account_id, fub_account_id, subscription_status, created_at, updated_at
            """
            
            result = await db_pool.fetchrow(update_query, fub_account_id)
            return dict(result) if result else None
        else:
            logger.info(f"Creating new account for FUB ID: {fub_account_id}")
            
            # Create new account
            insert_query = """
            INSERT INTO accounts (fub_account_id, subscription_status)
            VALUES ($1, $2)
            RETURNING account_id, fub_account_id, subscription_status, created_at, updated_at
            """
            
            result = await db_pool.fetchrow(insert_query, fub_account_id, "trialing")
            return dict(result) if result else None
            
    except Exception as e:
        logger.error(f"Error creating/updating account {fub_account_id}: {e}")
        return None


# Database connection pool
db_pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db_pool
    
    # Startup
    logger.info("Starting FUB Follow-up Assistant API")
    
    # Parse the DATABASE_URL to extract connection parameters
    import urllib.parse as urlparse
    database_url = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/fub_assistant')
    url = urlparse.urlparse(database_url)
    
    try:
        db_pool = await asyncpg.create_pool(
            host=url.hostname,
            port=url.port or 5432,
            user=url.username,
            password=url.password,
            database=url.path[1:] if url.path else 'fub_assistant',
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        logger.info("Database connection pool created successfully")
        
        # Test the connection
        async with db_pool.acquire() as connection:
            await connection.fetchval("SELECT 1")
        logger.info("Database connection test successful")
        
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        db_pool = None
    
    yield
    
    # Shutdown
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")


# Create FastAPI app
app = FastAPI(
    title="FUB Follow-up Assistant",
    description="AI-powered follow-up assistant for Follow Up Boss",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fub-followup-assistant-embed-plpgqa2jn.vercel.app",
        "https://*.followupboss.com", 
        "http://localhost:*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    try:
        if db_pool:
            async with db_pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
            db_status = "connected"
        else:
            db_status = "disconnected"
        
        return {
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy", 
            "database": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "FUB Follow-up Assistant API", 
        "version": "1.0.0",
        "status": "active"
    }


@app.post("/api/v1/setup-db")
async def setup_database() -> Dict[str, Any]:
    """Setup database tables."""
    try:
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database not connected")
        
        async with db_pool.acquire() as connection:
            # Create accounts table (matching original schema)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    fub_access_token TEXT,
                    fub_account_id VARCHAR(255) UNIQUE NOT NULL,
                    fub_refresh_token TEXT,
                    stripe_customer_id VARCHAR(255),
                    subscription_status VARCHAR(50) DEFAULT 'trialing',
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create chat_messages table (matching original schema)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    answer TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    person_id VARCHAR(255) NOT NULL,
                    question TEXT NOT NULL,
                    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant'))
                )
            """)
            
            # Create rate_limit_entries table
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS rate_limit_entries (
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    id SERIAL PRIMARY KEY,
                    identifier VARCHAR(255) NOT NULL,
                    request_count INTEGER DEFAULT 1,
                    window_start TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            
            # Create indexes for better performance
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_accounts_fub_account_id ON accounts(fub_account_id)
            """)
            
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_accounts_stripe_customer_id ON accounts(stripe_customer_id)
            """)
            
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_person_id ON chat_messages(person_id)
            """)
            
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at)
            """)
            
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_rate_limit_entries_identifier ON rate_limit_entries(identifier)
            """)
            
            await connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_rate_limit_entries_window_start ON rate_limit_entries(window_start)
            """)
        
        logger.info("Database setup completed successfully")
        return {"message": "Database setup completed", "status": "success"}
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database setup failed: {e}")


@app.get("/api/v1/test-db")
async def test_database() -> Dict[str, Any]:
    """Test database connectivity and return some stats."""
    try:
        if not db_pool:
            return {"status": "error", "message": "Database pool not initialized"}
        
        async with db_pool.acquire() as connection:
            # Test basic connectivity
            test_result = await connection.fetchval("SELECT 1")
            
            # Get table counts
            try:
                account_count = await connection.fetchval("SELECT COUNT(*) FROM accounts")
                chat_message_count = await connection.fetchval("SELECT COUNT(*) FROM chat_messages")
            except Exception:
                # Tables might not exist yet
                account_count = "N/A (table not found)"
                chat_message_count = "N/A (table not found)"
            
            return {
                "status": "success",
                "database_test": test_result,
                "account_count": account_count,
                "chat_message_count": chat_message_count,
                "pool_size": len(db_pool._holders) if hasattr(db_pool, '_holders') else "unknown"
            }
            
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/v1/auth/iframe-login", response_model=IframeLoginResponse)
async def iframe_login(request: IframeLoginRequest) -> IframeLoginResponse:
    """Authenticate iframe request and issue JWT token."""
    try:
        logger.info("=== IFRAME LOGIN START ===")
        logger.info(f"Request received - context length: {len(request.context)}, signature length: {len(request.signature)}")
        
        # Verify HMAC signature
        if not verify_hmac_signature(request.context, request.signature):
            logger.warning(f"Invalid HMAC signature for context: {request.context[:100]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        logger.info("HMAC signature verified successfully")
        
        # Parse context data
        try:
            # Decode base64 context first, then parse JSON
            import base64
            import binascii
            
            logger.info("=== BASE64 DECODING START ===")
            logger.info(f"Original context: {request.context}")
            
            # Fix base64 padding if needed (like the working app does)
            context_str = request.context
            original_length = len(context_str)
            padding = 4 - (len(context_str) % 4)
            if padding != 4:
                context_str += '=' * padding
                logger.info(f"Added {padding} padding characters")
            
            logger.info(f"Context length: {original_length} -> {len(context_str)}")
            
            decoded_context = base64.b64decode(context_str).decode('utf-8')
            logger.info(f"Decoded context length: {len(decoded_context)}")
            logger.info(f"Decoded context: {decoded_context}")
            
            context_data = json.loads(decoded_context)
            logger.info("=== BASE64 DECODING SUCCESS ===")
            logger.info(f"Parsed context data: {json.dumps(context_data, indent=2)}")
            
        except (json.JSONDecodeError, binascii.Error, UnicodeDecodeError) as e:
            logger.error(f"Failed to parse context data: {e}")
            logger.error(f"Context string: {request.context[:100]}...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid context data"
            )
        
        account_data = context_data.get("account", {})
        fub_account_id = str(account_data.get("id"))
        
        logger.info(f"Extracted FUB account ID: {fub_account_id}")
        
        if not fub_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing account ID in context"
            )
        
        # Create or get account
        logger.info("=== DATABASE OPERATIONS START ===")
        account = await create_or_update_account(fub_account_id)
        
        if not account:
            logger.error("Failed to create or get account")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account"
            )
        
        logger.info(f"Account operation successful: {account}")
        
        # Create JWT token
        token = create_jwt_token(
            account_id=account["account_id"],
            fub_account_id=fub_account_id,
            expires_delta=timedelta(hours=24)
        )
        
        logger.info("JWT token created successfully")
        logger.info("=== IFRAME LOGIN SUCCESS ===")
        
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


@app.post("/auth/callback", response_model=IframeLoginResponse)
async def fub_callback(request: IframeLoginRequest) -> IframeLoginResponse:
    """FUB callback endpoint - alias to iframe_login for FUB compatibility."""
    logger.info("=== FUB CALLBACK (/auth/callback) ===")
    logger.info(f"Received callback request with context length: {len(request.context)}")
    return await iframe_login(request)


@app.post("/auth/fub/callback", response_model=IframeLoginResponse)
async def fub_callback_alt(request: IframeLoginRequest) -> IframeLoginResponse:
    """Alternative FUB callback endpoint - handles /auth/fub/callback path."""
    logger.info("=== FUB CALLBACK ALT (/auth/fub/callback) ===")
    logger.info(f"Received callback request with context length: {len(request.context)}")
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


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with detailed information."""
    start_time = datetime.utcnow()
    
    # Log request details
    logger.info("=== INCOMING REQUEST ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Path: {request.url.path}")
    logger.info(f"Query params: {dict(request.query_params)}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Client IP: {request.client.host if request.client else 'unknown'}")
    
    # Log body for POST requests
    if request.method == "POST":
        try:
            body = await request.body()
            logger.info(f"Body length: {len(body)}")
            if len(body) < 2000:  # Only log small bodies
                logger.info(f"Body content: {body.decode('utf-8')}")
            else:
                logger.info(f"Body too large to log ({len(body)} bytes)")
        except Exception as e:
            logger.error(f"Error reading request body: {e}")
    
    # Process request
    response = await call_next(request)
    
    # Remove restrictive headers that prevent iframe embedding
    # Allow iframe embedding from Follow Up Boss
    response.headers.pop('X-Frame-Options', None)
    response.headers.pop('Content-Security-Policy', None)
    
    # Log response
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=== RESPONSE ===")
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Duration: {duration:.3f}s")
    logger.info(f"Response headers: {dict(response.headers)}")
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 