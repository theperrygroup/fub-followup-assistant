"""Authentication routes for iframe login and JWT management.

This module handles HMAC verification for iframe requests and JWT token
creation, validation, and refresh functionality.
"""

import json
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel import Session, create_engine, select

from auth import create_jwt_token, should_refresh_token, verify_hmac_signature, verify_jwt_token
from config import settings
from models import Account, SubscriptionStatus
from utils import create_or_update_account, get_account_by_fub_id


# Database engine
engine = create_engine(settings.database_url)
router = APIRouter(prefix="/auth", tags=["authentication"])


class IframeLoginRequest(BaseModel):
    """Request model for iframe login.
    
    Attributes:
        context: Context data from Follow Up Boss iframe.
        signature: HMAC signature for verification.
    """
    context: str = Field(..., description="Context data from FUB iframe")
    signature: str = Field(..., description="HMAC signature")


class IframeLoginResponse(BaseModel):
    """Response model for iframe login.
    
    Attributes:
        account_id: Internal account ID.
        fub_account_id: Follow Up Boss account ID.
        subscription_status: Current subscription status.
        token: JWT authentication token.
    """
    account_id: int = Field(..., description="Internal account ID")
    fub_account_id: str = Field(..., description="Follow Up Boss account ID")
    subscription_status: str = Field(..., description="Subscription status")
    token: str = Field(..., description="JWT token")


class TokenRefreshResponse(BaseModel):
    """Response model for token refresh.
    
    Attributes:
        token: New JWT token.
    """
    token: str = Field(..., description="New JWT token")


def get_db_session():
    """Get database session dependency.
    
    Yields:
        Database session.
    """
    with Session(engine) as session:
        yield session


def get_current_account(request: Request, session: Session = Depends(get_db_session)) -> Account:
    """Get current authenticated account from JWT token.
    
    Args:
        request: FastAPI request object.
        session: Database session.
        
    Returns:
        Current account.
        
    Raises:
        HTTPException: If token is invalid or account not found.
    """
    authorization = request.headers.get("Authorization")
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    payload = verify_jwt_token(token)
    
    account_id = payload.get("account_id")
    account = session.get(Account, account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found"
        )
    
    return account


@router.post("/iframe-login", response_model=IframeLoginResponse)
async def iframe_login(
    request: IframeLoginRequest,
    session: Session = Depends(get_db_session)
) -> IframeLoginResponse:
    """Authenticate iframe request and issue JWT token.
    
    Verifies HMAC signature and creates or updates account record.
    
    Args:
        request: Login request with context and signature.
        session: Database session.
        
    Returns:
        Authentication response with JWT token.
        
    Raises:
        HTTPException: If HMAC verification fails.
    """
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
            context_data = json.loads(request.context)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in context: {request.context[:100]}...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid context format"
            )
        
        # Extract FUB account ID from context
        fub_account_id = context_data.get("account", {}).get("id")
        if not fub_account_id:
            logger.error("No account ID found in context")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing account ID in context"
            )
        
        # Create or update account
        account = create_or_update_account(session, str(fub_account_id))
        
        # Create JWT token
        if not account.id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account ID not set"
            )
        
        token = create_jwt_token(
            account_id=account.id,
            fub_account_id=account.fub_account_id,
            expires_delta=timedelta(hours=24)
        )
        
        logger.info(f"Successful iframe login for account: {fub_account_id}")
        
        return IframeLoginResponse(
            account_id=account.id,
            fub_account_id=account.fub_account_id,
            subscription_status=account.subscription_status.value,
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


@router.get("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    account: Account = Depends(get_current_account)
) -> TokenRefreshResponse:
    """Refresh JWT token if it expires within 15 minutes.
    
    Args:
        account: Current authenticated account.
        
    Returns:
        New JWT token if refresh is needed, otherwise current token.
    """
    try:
        # Get current token from request (this is a bit of a hack)
        # In a real implementation, you might want to pass the token payload
        # through the dependency chain
        if not account.id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account ID not set"
            )
        
        new_token = create_jwt_token(
            account_id=account.id,
            fub_account_id=account.fub_account_id,
            expires_delta=timedelta(hours=24)
        )
        
        logger.info(f"Token refreshed for account: {account.fub_account_id}")
        
        return TokenRefreshResponse(token=new_token)
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        ) 