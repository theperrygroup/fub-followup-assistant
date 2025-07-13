"""Authentication and authorization utilities.

This module handles HMAC signature verification for iframe requests,
JWT token creation and validation, and Follow Up Boss OAuth integration.
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt
from loguru import logger

from config import settings


class AuthenticationError(Exception):
    """Custom authentication error."""
    pass


def verify_hmac_signature(context: str, signature: str) -> bool:
    """Verify HMAC signature from Follow Up Boss iframe.
    
    Args:
        context: The context data from the iframe.
        signature: The HMAC signature to verify.
        
    Returns:
        True if signature is valid, False otherwise.
    """
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
    """Create a JWT token for the authenticated user.
    
    Args:
        account_id: Internal account ID.
        fub_account_id: Follow Up Boss account ID.
        expires_delta: Token expiration time delta.
        
    Returns:
        Encoded JWT token.
    """
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
    """Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify.
        
    Returns:
        Decoded token payload.
        
    Raises:
        HTTPException: If token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        account_id: int = payload.get("account_id")
        fub_account_id: str = payload.get("fub_account_id")
        
        if account_id is None or fub_account_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def should_refresh_token(token_payload: dict) -> bool:
    """Check if JWT token should be refreshed.
    
    Args:
        token_payload: Decoded JWT payload.
        
    Returns:
        True if token should be refreshed (expires in < 15 minutes).
    """
    exp = token_payload.get("exp")
    if not exp:
        return True
    
    expires_at = datetime.fromtimestamp(exp)
    time_until_expiry = expires_at - datetime.utcnow()
    
    return time_until_expiry < timedelta(minutes=15)


async def refresh_fub_tokens(refresh_token: str) -> tuple[str, str]:
    """Refresh Follow Up Boss OAuth tokens.
    
    Args:
        refresh_token: The refresh token to use.
        
    Returns:
        Tuple of (new_access_token, new_refresh_token).
        
    Raises:
        AuthenticationError: If token refresh fails.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.followupboss.com/v1/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.fub_client_id,
                    "client_secret": settings.fub_client_secret,
                }
            )
            
            if response.status_code != 200:
                logger.error(f"FUB token refresh failed: {response.status_code} {response.text}")
                raise AuthenticationError("Failed to refresh tokens")
            
            data = response.json()
            return data["access_token"], data["refresh_token"]
            
        except httpx.RequestError as e:
            logger.error(f"FUB token refresh request error: {e}")
            raise AuthenticationError("Failed to refresh tokens")


async def make_fub_api_request(
    access_token: str,
    refresh_token: str,
    url: str,
    method: str = "GET",
    **kwargs
) -> tuple[dict, str, str]:
    """Make an authenticated request to Follow Up Boss API with automatic token refresh.
    
    Args:
        access_token: Current access token.
        refresh_token: Current refresh token.
        url: API endpoint URL.
        method: HTTP method.
        **kwargs: Additional request parameters.
        
    Returns:
        Tuple of (response_data, new_access_token, new_refresh_token).
        
    Raises:
        AuthenticationError: If request fails after token refresh.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(method, url, headers=headers, **kwargs)
            
            # If unauthorized, try refreshing tokens once
            if response.status_code == 401:
                logger.info("FUB API returned 401, refreshing tokens")
                new_access_token, new_refresh_token = await refresh_fub_tokens(refresh_token)
                
                # Retry with new token
                headers["Authorization"] = f"Bearer {new_access_token}"
                response = await client.request(method, url, headers=headers, **kwargs)
                
                if response.status_code != 200:
                    logger.error(f"FUB API request failed after refresh: {response.status_code} {response.text}")
                    raise AuthenticationError("API request failed")
                
                return response.json(), new_access_token, new_refresh_token
            
            if response.status_code != 200:
                logger.error(f"FUB API request failed: {response.status_code} {response.text}")
                raise AuthenticationError("API request failed")
            
            return response.json(), access_token, refresh_token
            
        except httpx.RequestError as e:
            logger.error(f"FUB API request error: {e}")
            raise AuthenticationError("API request failed") 