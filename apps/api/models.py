"""Database models for the FUB Follow-up Assistant.

This module contains all SQLModel models representing database tables.
All fields are alphabetically sorted with required fields first.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    UNPAID = "unpaid"


class Account(SQLModel, table=True):
    """Account model representing a Follow Up Boss account."""
    
    __tablename__ = "accounts"
    
    # Primary key
    account_id: Optional[int] = Field(primary_key=True)
    
    # Required fields
    fub_account_id: str = Field(unique=True, index=True)
    subscription_status: SubscriptionStatus = Field(default=SubscriptionStatus.TRIALING)
    
    # Optional fields
    fub_access_token: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    fub_refresh_token: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatMessage(SQLModel, table=True):
    """Chat message model for storing conversation history."""
    
    __tablename__ = "chat_messages"
    
    # Primary key
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    
    # Required fields
    person_id: str = Field(index=True)
    question: str
    role: str  # 'user' or 'assistant'
    
    # Optional fields
    answer: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class RateLimitEntry(SQLModel, table=True):
    """Rate limiting entry for API requests."""
    
    __tablename__ = "rate_limit_entries"
    
    # Primary key
    id: Optional[int] = Field(primary_key=True)
    
    # Required fields
    identifier: str = Field(index=True)
    window_start: datetime
    request_count: int = Field(default=1)
    
    # Optional fields
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow) 