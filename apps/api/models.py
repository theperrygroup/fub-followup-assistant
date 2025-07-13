"""Database models for the FUB Follow-up Assistant.

This module contains all SQLModel models representing database tables.
All fields are alphabetically sorted with required fields first.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import Field
from sqlmodel import Column, DateTime, SQLModel, Text, func


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    UNPAID = "unpaid"


class Account(SQLModel, table=True):
    """Account model representing a Follow Up Boss account.
    
    Attributes:
        fub_account_id: Follow Up Boss account ID.
        subscription_status: Current subscription status.
        fub_access_token: OAuth access token (encrypted).
        created_at: Account creation timestamp.
        fub_refresh_token: OAuth refresh token (encrypted).
        stripe_customer_id: Stripe customer ID.
        updated_at: Last update timestamp.
        account_id: Primary key.
    """
    
    __tablename__ = "accounts"
    
    # Required fields (alphabetical)
    fub_account_id: str = Field(unique=True, index=True)
    subscription_status: SubscriptionStatus = Field(default=SubscriptionStatus.TRIALING)
    
    # Optional fields (alphabetical)
    fub_access_token: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    fub_refresh_token: Optional[str] = Field(default=None, sa_column=Column(Text))
    stripe_customer_id: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), onupdate=func.now()))
    
    # Primary key
    account_id: int = Field(primary_key=True)


class ChatMessage(SQLModel, table=True):
    """Chat message model for storing conversation history.
    
    Attributes:
        person_id: Follow Up Boss person ID.
        question: User question.
        role: Message role (user or assistant).
        answer: AI response.
        created_at: Message timestamp.
        id: Primary key (UUID).
    """
    
    __tablename__ = "chat_messages"
    
    # Required fields (alphabetical)
    person_id: str = Field(index=True)
    question: str = Field(sa_column=Column(Text))
    role: str = Field()  # 'user' or 'assistant'
    
    # Optional fields (alphabetical)
    answer: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    
    # Primary key (UUID)
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)


class RateLimitEntry(SQLModel, table=True):
    """Rate limiting entry for API requests.
    
    Attributes:
        identifier: Rate limit identifier (account_id or ip_address).
        window_start: Rate limit window start time.
        request_count: Number of requests in current window.
        created_at: Entry creation timestamp.
        id: Primary key.
    """
    
    __tablename__ = "rate_limit_entries"
    
    # Required fields (alphabetical)
    identifier: str = Field(index=True)
    window_start: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    request_count: int = Field(default=1)
    
    # Optional fields (alphabetical)
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    
    # Primary key
    id: int = Field(primary_key=True) 