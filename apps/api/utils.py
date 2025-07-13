"""Utility functions for the application.

This module contains helper functions for rate limiting, database operations,
and other common utilities used across the application.
"""

import json
from datetime import datetime, timedelta
from typing import Optional

import redis.asyncio as redis
from loguru import logger
from sqlmodel import Session, select

from config import settings
from models import Account, RateLimitEntry


# Global Redis connection
redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get Redis client instance.
    
    Returns:
        Redis client instance.
    """
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.redis_url)
    return redis_client


async def check_rate_limit(key: str, max_requests: int, window_minutes: int = 1) -> bool:
    """Check if request is within rate limit using token bucket algorithm.
    
    Args:
        key: Unique key for rate limiting (account_id or ip_address).
        max_requests: Maximum requests allowed in the window.
        window_minutes: Time window in minutes.
        
    Returns:
        True if request is allowed, False if rate limited.
    """
    try:
        redis_conn = await get_redis_client()
        
        # Use Redis for high-performance rate limiting
        pipe = redis_conn.pipeline()
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Sliding window rate limiting
        pipe.zremrangebyscore(f"rate_limit:{key}", 0, window_start.timestamp())
        pipe.zcard(f"rate_limit:{key}")
        pipe.zadd(f"rate_limit:{key}", {str(now.timestamp()): now.timestamp()})
        pipe.expire(f"rate_limit:{key}", window_minutes * 60)
        
        results = await pipe.execute()
        current_requests = results[1]
        
        return current_requests < max_requests
        
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        # If Redis fails, allow the request (fail open)
        return True


async def get_cached_lead_data(person_id: str) -> Optional[dict]:
    """Get cached lead data from Redis.
    
    Args:
        person_id: Follow Up Boss person ID.
        
    Returns:
        Cached lead data or None if not found/expired.
    """
    try:
        redis_conn = await get_redis_client()
        cached_data = await redis_conn.get(f"lead_data:{person_id}")
        
        if cached_data:
            return json.loads(cached_data)
        
        return None
        
    except Exception as e:
        logger.error(f"Redis cache get error: {e}")
        return None


async def cache_lead_data(person_id: str, data: dict, ttl_seconds: int = 90) -> None:
    """Cache lead data in Redis.
    
    Args:
        person_id: Follow Up Boss person ID.
        data: Lead data to cache.
        ttl_seconds: Time to live in seconds.
    """
    try:
        redis_conn = await get_redis_client()
        await redis_conn.setex(
            f"lead_data:{person_id}",
            ttl_seconds,
            json.dumps(data, default=str)
        )
        
    except Exception as e:
        logger.error(f"Redis cache set error: {e}")


def format_chat_response(response: str) -> str:
    """Format AI chat response to meet requirements.
    
    Args:
        response: Raw AI response.
        
    Returns:
        Formatted response (≤ 3 bullets, ≤ 400 chars).
    """
    # Split into lines and take first 3
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    
    # Ensure we have bullet points
    formatted_lines = []
    for i, line in enumerate(lines[:3]):
        if not line.startswith('•') and not line.startswith('-'):
            line = f"• {line}"
        formatted_lines.append(line)
    
    # Join and truncate to 400 characters
    result = '\n'.join(formatted_lines)
    
    if len(result) > 400:
        result = result[:397] + "..."
    
    return result


def summarize_lead_activities(activities: list) -> str:
    """Summarize lead activities for AI context.
    
    Args:
        activities: List of lead activities from FUB API.
        
    Returns:
        Summarized activities string.
    """
    if not activities:
        return "No recent activities found."
    
    # Group activities by type
    activity_groups: dict[str, list] = {
        'calls': [],
        'texts': [],
        'emails': [],
        'notes': []
    }
    
    for activity in activities[-5:]:  # Last 5 activities
        activity_type = activity.get('type', '').lower()
        
        if 'call' in activity_type:
            activity_groups['calls'].append(activity)
        elif 'text' in activity_type or 'sms' in activity_type:
            activity_groups['texts'].append(activity)
        elif 'email' in activity_type:
            activity_groups['emails'].append(activity)
        elif 'note' in activity_type:
            activity_groups['notes'].append(activity)
    
    summary_parts = []
    
    for activity_type, items in activity_groups.items():
        if items:
            count = len(items)
            latest = items[-1]
            date = latest.get('created', '')
            summary_parts.append(f"{count} {activity_type} (latest: {date})")
    
    return "; ".join(summary_parts) if summary_parts else "No recent activities found."


def get_account_by_fub_id(session: Session, fub_account_id: str) -> Optional[Account]:
    """Get account by Follow Up Boss account ID.
    
    Args:
        session: Database session.
        fub_account_id: Follow Up Boss account ID.
        
    Returns:
        Account instance or None if not found.
    """
    statement = select(Account).where(Account.fub_account_id == fub_account_id)
    return session.exec(statement).first()


def create_or_update_account(session: Session, fub_account_id: str, **kwargs) -> Account:
    """Create or update an account.
    
    Args:
        session: Database session.
        fub_account_id: Follow Up Boss account ID.
        **kwargs: Additional account fields to update.
        
    Returns:
        Account instance.
    """
    account = get_account_by_fub_id(session, fub_account_id)
    
    if account:
        # Update existing account
        for key, value in kwargs.items():
            if hasattr(account, key):
                setattr(account, key, value)
        account.updated_at = datetime.utcnow()
    else:
        # Create new account
        account = Account(fub_account_id=fub_account_id, **kwargs)
        session.add(account)
    
    session.commit()
    session.refresh(account)
    return account 