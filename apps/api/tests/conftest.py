"""
Pytest configuration and shared fixtures for FUB Follow-up Assistant API tests.

This module provides all necessary fixtures for testing the FastAPI application,
including database setup, authentication, mocking external services, and test clients.
"""

import asyncio
import asyncpg
import pytest
import redis.asyncio as redis
from fastapi.testclient import TestClient
from httpx import AsyncClient
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
import uuid
from faker import Faker
import jwt

# Import application modules
from main import app
from config import settings
from models import Account, ChatMessage

# Initialize faker for generating test data
fake = Faker()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_settings():
    """Provide test-specific application settings."""
    # Override with test-specific values
    test_settings = {
        "app_env": "test",
        "database_url": "postgresql://test:test@localhost:5433/test_db", 
        "redis_url": "redis://localhost:6379/1",
        "openai_api_key": "test-key",
        "stripe_secret_key": "sk_test_fake"
    }
    return test_settings


@pytest.fixture(scope="session")
async def test_db_pool(test_settings) -> AsyncGenerator[asyncpg.Pool, None]:
    """Create a test database connection pool."""
    pool = await asyncpg.create_pool(
        test_settings["database_url"],
        min_size=1,
        max_size=5
    )
    
    # Clean and setup test database
    async with pool.acquire() as conn:
        # Drop all tables
        await conn.execute("""
            DROP SCHEMA IF EXISTS public CASCADE;
            CREATE SCHEMA public;
        """)
        
        # Create tables
        await conn.execute("""
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
            
            CREATE TABLE IF NOT EXISTS chat_messages (
                answer TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                person_id VARCHAR(255) NOT NULL,
                question TEXT NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant'))
            );
            
            CREATE TABLE IF NOT EXISTS rate_limit_entries (
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                id SERIAL PRIMARY KEY,
                identifier VARCHAR(255) NOT NULL,
                request_count INTEGER DEFAULT 1,
                window_start TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """)
    
    yield pool
    await pool.close()


@pytest.fixture(scope="session")
async def test_redis_client(test_settings) -> AsyncGenerator[redis.Redis, None]:
    """Create a test Redis client."""
    client = redis.from_url(test_settings["redis_url"])
    
    # Clear test database
    await client.flushdb()
    
    yield client
    await client.close()


@pytest.fixture
async def db_transaction(test_db_pool) -> AsyncGenerator[asyncpg.Connection, None]:
    """Provide a database transaction that rolls back after each test."""
    async with test_db_pool.acquire() as conn:
        async with conn.transaction():
            yield conn
            # Transaction will automatically rollback


@pytest.fixture
def test_client() -> TestClient:
    """Provide a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_account_data() -> Dict[str, Any]:
    """Provide sample account data for testing."""
    return {
        "fub_account_id": fake.uuid4(),
        "fub_access_token": fake.sha256(),
        "fub_refresh_token": fake.sha256(),
        "stripe_customer_id": f"cus_{fake.lexify('?' * 14)}",
        "subscription_status": "active"
    }


@pytest.fixture
async def test_account(db_transaction, sample_account_data) -> Dict[str, Any]:
    """Create a test account in the database."""
    account_id = await db_transaction.fetchval("""
        INSERT INTO accounts (fub_account_id, fub_access_token, fub_refresh_token, 
                            stripe_customer_id, subscription_status)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING account_id
    """, 
        sample_account_data["fub_account_id"],
        sample_account_data["fub_access_token"],
        sample_account_data["fub_refresh_token"], 
        sample_account_data["stripe_customer_id"],
        sample_account_data["subscription_status"]
    )
    
    return {**sample_account_data, "account_id": account_id}


@pytest.fixture
def sample_chat_message_data() -> Dict[str, Any]:
    """Provide sample chat message data for testing."""
    return {
        "person_id": fake.uuid4(),
        "question": fake.text(max_nb_chars=200),
        "answer": fake.text(max_nb_chars=500),
        "role": fake.random_element(["user", "assistant"])
    }


@pytest.fixture
def sample_lead_context() -> Dict[str, Any]:
    """Provide sample Follow Up Boss lead context for testing."""
    return {
        "id": fake.uuid4(),
        "firstName": fake.first_name(),
        "lastName": fake.last_name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "status": fake.random_element(["New", "Contacted", "Qualified"]),
        "source": fake.random_element(["Website", "Referral", "Advertisement"]),
        "tags": [fake.word() for _ in range(3)],
        "customFields": {
            "budget": fake.random_int(100000, 1000000),
            "location": fake.city()
        }
    }


@pytest.fixture
def auth_headers(test_account) -> Dict[str, str]:
    """Provide authentication headers for API requests."""
    # Create a simple test JWT token
    payload = {
        "account_id": test_account["account_id"],
        "fub_account_id": test_account["fub_account_id"],
        "exp": fake.future_datetime().timestamp()
    }
    
    token = jwt.encode(payload, "test-secret-key", algorithm="HS256")
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("openai.OpenAI") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        # Mock chat completion
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = fake.text(max_nb_chars=500)
        mock_response.usage.total_tokens = fake.random_int(100, 1000)
        
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        
        yield mock_instance


@pytest.fixture 
def mock_stripe():
    """Mock Stripe API calls."""
    with patch("stripe.Customer") as mock_customer, \
         patch("stripe.Subscription") as mock_subscription, \
         patch("stripe.Webhook") as mock_webhook:
        
        # Mock customer creation
        mock_customer.create.return_value = Mock(id=f"cus_{fake.lexify('?' * 14)}")
        
        # Mock subscription creation
        mock_subscription.create.return_value = Mock(
            id=f"sub_{fake.lexify('?' * 14)}",
            status="active",
            current_period_end=fake.future_datetime().timestamp()
        )
        
        # Mock webhook verification
        mock_webhook.construct_event.return_value = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": f"sub_{fake.lexify('?' * 14)}",
                    "customer": f"cus_{fake.lexify('?' * 14)}",
                    "status": "active"
                }
            }
        }
        
        yield {
            "customer": mock_customer,
            "subscription": mock_subscription, 
            "webhook": mock_webhook
        }


@pytest.fixture
def mock_fub_api():
    """Mock Follow Up Boss API calls."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = Mock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # Mock successful API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": fake.uuid4(),
            "type": "note",
            "body": fake.text(max_nb_chars=200),
            "created": fake.iso8601()
        }
        
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_instance.get = AsyncMock(return_value=mock_response)
        
        yield mock_instance


@pytest.fixture
def mock_redis(test_redis_client):
    """Mock Redis operations for rate limiting tests."""
    return test_redis_client


@pytest.fixture(autouse=True)
async def setup_test_environment(test_db_pool, test_redis_client):
    """Automatically set up and clean test environment for each test."""
    # Set global database pool and Redis client for the app
    app.state.db_pool = test_db_pool
    app.state.redis_client = test_redis_client
    
    yield
    
    # Clean up after test
    await test_redis_client.flushdb()


# Pytest markers for categorizing tests
pytestmark = [
    pytest.mark.asyncio,
] 