"""Test configuration and fixtures for the FUB Follow-up Assistant API.

This module provides shared test fixtures, configurations, and utilities for testing
the FastAPI application including database, Redis, and authentication mocking.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

import pytest
import pytest_asyncio
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel, Session, create_engine

from config import Settings
from models import Account, SubscriptionStatus

fake = Faker()

# Test database configuration
TEST_DATABASE_URL = "sqlite:///test.db"
TEST_REDIS_URL = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session") 
def test_settings():
    """Create test settings with overridden values."""
    # Clear any existing environment variables
    test_env = {
        "APP_ENV": "test",
        "DATABASE_URL": TEST_DATABASE_URL,
        "FRONTEND_EMBED_ORIGIN": "https://test-app.example.com",
        "FUB_CLIENT_ID": "placeholder-client-id",
        "FUB_CLIENT_SECRET": "test-client-secret", 
        "FUB_EMBED_SECRET": "test-embed-secret",
        "JWT_SECRET": "test-jwt-secret",
        "MARKETING_ORIGIN": "https://test.example.com",
        "OPENAI_API_KEY": "sk-test-key",
        "REDIS_URL": TEST_REDIS_URL,
        "STRIPE_PRICE_ID_MONTHLY": "price_test123",
        "STRIPE_SECRET_KEY": "sk_test_stripe",
        "STRIPE_WEBHOOK_SECRET": "whsec_test"
    }
    
    # Temporarily set environment variables
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        settings = Settings()
        yield settings
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@pytest.fixture
def test_app():
    """Create a FastAPI test application with all routes."""
    # Import here to avoid circular imports
    from main import app
    return app


@pytest.fixture  
def client(test_app):
    """Create a test client for the FastAPI app."""
    return TestClient(test_app)


@pytest_asyncio.fixture
async def redis_client():
    """Create a mock Redis client for async tests."""
    redis_mock = AsyncMock()
    
    # Mock async methods
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.ping = AsyncMock(return_value=True)
    
    # Mock pipeline  
    pipeline_mock = AsyncMock()
    pipeline_mock.get = AsyncMock(return_value=None)
    pipeline_mock.incr = AsyncMock(return_value=1)
    pipeline_mock.expire = AsyncMock(return_value=True)
    pipeline_mock.execute = AsyncMock(return_value=[None, 1, True])
    redis_mock.pipeline = AsyncMock(return_value=pipeline_mock)
    
    yield redis_mock


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session
    
    # Clean up
    SQLModel.metadata.drop_all(engine)


@pytest.fixture  # Changed from @pytest_asyncio.fixture since this is not async
def db_transaction(db_session):
    """Create a database transaction that rolls back after test."""
    transaction = db_session.begin()
    yield db_session
    transaction.rollback()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client with common methods for sync tests."""
    redis_mock = Mock()
    
    # Mock async methods
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.ping = AsyncMock(return_value=True)
    
    # Mock pipeline
    pipeline_mock = Mock()
    pipeline_mock.get = Mock()
    pipeline_mock.incr = Mock()
    pipeline_mock.expire = Mock()
    pipeline_mock.execute = AsyncMock(return_value=[None, 1, None, None])
    redis_mock.pipeline = Mock(return_value=pipeline_mock)
    
    return redis_mock


@pytest.fixture
def sample_account_data():
    """Generate sample account data for testing."""
    return {
        "fub_account_id": str(fake.uuid4()),
        "subscription_status": SubscriptionStatus.ACTIVE,
        "fub_access_token": fake.sha256(),
        "fub_refresh_token": fake.sha256(),
        "stripe_customer_id": f"cus_{fake.lexify('??' * 12)}"
    }


@pytest.fixture  # Changed from @pytest_asyncio.fixture since this is not async
def test_account(db_session, sample_account_data):
    """Create a test account in the database."""
    account = Account(**sample_account_data)
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    yield account


@pytest.fixture
def sample_chat_message_data():
    """Generate sample chat message data for testing."""
    return {
        "person_id": str(fake.uuid4()),
        "question": fake.text(max_nb_chars=200),
        "role": fake.random_element(elements=("user", "assistant")),
        "answer": fake.text(max_nb_chars=400)
    }


@pytest.fixture
def auth_headers():
    """Generate test authentication headers."""
    return {
        "Authorization": f"Bearer {fake.sha256()}",
        "X-FUB-Account-ID": str(fake.uuid4())
    }


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = Mock()
    
    # Mock chat completions
    completion_mock = Mock()
    completion_mock.choices = [Mock()]
    completion_mock.choices[0].message = Mock()
    completion_mock.choices[0].message.content = "Mocked AI response"
    
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock(return_value=completion_mock)
    
    return client


@pytest.fixture
def mock_stripe_client():
    """Create a mock Stripe client."""
    stripe_mock = Mock()
    
    # Mock customer operations
    stripe_mock.Customer = Mock()
    stripe_mock.Customer.create = Mock(return_value={"id": "cus_test123"})
    stripe_mock.Customer.retrieve = Mock(return_value={"id": "cus_test123", "email": "test@example.com"})
    stripe_mock.Customer.modify = Mock(return_value={"id": "cus_test123"})
    
    # Mock subscription operations
    stripe_mock.Subscription = Mock()
    stripe_mock.Subscription.create = Mock(return_value={"id": "sub_test123", "status": "active"})
    stripe_mock.Subscription.retrieve = Mock(return_value={"id": "sub_test123", "status": "active"})
    stripe_mock.Subscription.modify = Mock(return_value={"id": "sub_test123"})
    stripe_mock.Subscription.cancel = Mock(return_value={"id": "sub_test123", "status": "canceled"})
    
    # Mock webhook operations
    stripe_mock.Webhook = Mock()
    stripe_mock.Webhook.construct_event = Mock(return_value={"type": "invoice.payment_succeeded"})
    
    return stripe_mock


@pytest.fixture
def mock_fub_api():
    """Create a mock Follow Up Boss API client."""
    api_mock = Mock()
    
    # Mock authentication
    api_mock.get_access_token = AsyncMock(return_value={
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "expires_in": 3600
    })
    
    # Mock person/lead data
    api_mock.get_person = AsyncMock(return_value={
        "id": "person_123",
        "name": "John Doe", 
        "email": "john@example.com",
        "phone": "+1234567890"
    })
    
    # Mock activities data
    api_mock.get_person_activities = AsyncMock(return_value=[
        {
            "id": "activity_1",
            "type": "call",
            "created": "2024-01-01T10:00:00Z",
            "note": "Called about property inquiry"
        },
        {
            "id": "activity_2", 
            "type": "email",
            "created": "2024-01-02T14:30:00Z",
            "note": "Sent listing information"
        }
    ])
    
    return api_mock


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables automatically for all tests."""
    test_env_vars = {
        "APP_ENV": "test",
        "DATABASE_URL": TEST_DATABASE_URL,
        "REDIS_URL": TEST_REDIS_URL,
        "OPENAI_API_KEY": "sk-test-key",
        "FUB_CLIENT_ID": "placeholder-client-id",
        "FUB_CLIENT_SECRET": "test-client-secret",
        "STRIPE_SECRET_KEY": "sk_test_stripe",
        "JWT_SECRET": "test-jwt-secret",
        "FUB_EMBED_SECRET": "test-embed-secret",
        "STRIPE_WEBHOOK_SECRET": "whsec_test",
        "STRIPE_PRICE_ID_MONTHLY": "price_test123",
        "FRONTEND_EMBED_ORIGIN": "https://test-app.example.com",
        "MARKETING_ORIGIN": "https://test.example.com"
    }
    
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value) 