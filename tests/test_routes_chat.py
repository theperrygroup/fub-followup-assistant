"""Tests for chat routes.

This module tests all chat endpoints including AI-powered lead follow-up
assistance, subscription checks, and rate limiting functionality.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from routes.chat import (
    ChatRequest, ChatResponse, check_subscription_active,
    apply_rate_limiting, chat
)
from models import Account, SubscriptionStatus


class TestPydanticModels:
    """Test Pydantic request/response models."""

    def test_chat_request_valid(self):
        """Test ChatRequest model with valid data."""
        data = {
            "person_id": "person_123",
            "question": "How should I follow up with this lead?"
        }
        request = ChatRequest(**data)
        assert request.person_id == "person_123"
        assert request.question == "How should I follow up with this lead?"

    def test_chat_request_max_length_validation(self):
        """Test ChatRequest question max length validation."""
        long_question = "x" * 1001  # Exceeds 1000 character limit
        
        with pytest.raises(ValueError):
            ChatRequest(person_id="person_123", question=long_question)

    def test_chat_response_valid(self):
        """Test ChatResponse model with valid data."""
        data = {
            "answer": "Here are some follow-up suggestions...",
            "person_id": "person_123"
        }
        response = ChatResponse(**data)
        assert response.answer == "Here are some follow-up suggestions..."
        assert response.person_id == "person_123"


class TestSubscriptionCheck:
    """Test subscription status checking."""

    @pytest.mark.asyncio
    async def test_check_subscription_active_success(self):
        """Test subscription check with active subscription."""
        account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        
        # Should not raise exception
        await check_subscription_active(account)

    @pytest.mark.asyncio
    async def test_check_subscription_trialing_success(self):
        """Test subscription check with trialing subscription."""
        account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.trialing
        )
        
        # Should not raise exception
        await check_subscription_active(account)

    @pytest.mark.asyncio
    async def test_check_subscription_inactive_failure(self):
        """Test subscription check with inactive subscription."""
        account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.cancelled
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await check_subscription_active(account)
        
        assert exc_info.value.status_code == 403
        assert "active subscription" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_check_subscription_past_due_failure(self):
        """Test subscription check with past due subscription."""
        account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.past_due
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await check_subscription_active(account)
        
        assert exc_info.value.status_code == 403


class TestRateLimiting:
    """Test rate limiting functionality."""

    @patch('routes.chat.check_rate_limit')
    @pytest.mark.asyncio
    async def test_apply_rate_limiting_within_limit(self, mock_check_rate_limit):
        """Test rate limiting when within limits."""
        mock_check_rate_limit.return_value = True
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        
        account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        
        # Should not raise exception
        await apply_rate_limiting(mock_request, account)
        
        # Verify rate limit was checked
        mock_check_rate_limit.assert_called_once()

    @patch('routes.chat.check_rate_limit')
    @pytest.mark.asyncio
    async def test_apply_rate_limiting_exceeded(self, mock_check_rate_limit):
        """Test rate limiting when limits are exceeded."""
        mock_check_rate_limit.return_value = False
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        
        account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await apply_rate_limiting(mock_request, account)
        
        assert exc_info.value.status_code == 429
        assert "rate limit" in exc_info.value.detail.lower()

    @patch('routes.chat.check_rate_limit')
    @pytest.mark.asyncio
    async def test_apply_rate_limiting_no_client_ip(self, mock_check_rate_limit):
        """Test rate limiting when client IP is not available."""
        mock_check_rate_limit.return_value = True
        mock_request = Mock()
        mock_request.client = None  # No client IP
        
        account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        
        # Should handle missing client gracefully
        await apply_rate_limiting(mock_request, account)


class TestChatEndpoint:
    """Test chat endpoint functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.chat.apply_rate_limiting')
    @patch('routes.chat.check_subscription_active')
    @patch('routes.chat.ChatService')
    @patch('routes.chat.get_current_account')
    def test_chat_success(self, mock_get_account, mock_chat_service_class,
                         mock_check_subscription, mock_rate_limiting, client):
        """Test successful chat request."""
        # Setup mocks
        mock_account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        mock_get_account.return_value = mock_account
        mock_rate_limiting.return_value = None
        mock_check_subscription.return_value = None
        
        # Mock chat service
        mock_chat_service = Mock()
        mock_chat_service.generate_response.return_value = "Here's my advice on following up..."
        mock_chat_service_class.return_value = mock_chat_service
        
        request_data = {
            "person_id": "person_123",
            "question": "How should I follow up with this lead?"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/chat", json=request_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Here's my advice on following up..."
        assert data["person_id"] == "person_123"

    @patch('routes.chat.get_current_account')
    def test_chat_no_auth(self, mock_get_account, client):
        """Test chat endpoint without authentication."""
        mock_get_account.side_effect = HTTPException(status_code=401, detail="Unauthorized")
        
        request_data = {
            "person_id": "person_123",
            "question": "Test question"
        }
        
        response = client.post("/chat", json=request_data)
        assert response.status_code == 401

    @patch('routes.chat.get_current_account')
    @patch('routes.chat.check_subscription_active')
    def test_chat_inactive_subscription(self, mock_check_subscription, mock_get_account, client):
        """Test chat endpoint with inactive subscription."""
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.cancelled
        )
        mock_get_account.return_value = mock_account
        mock_check_subscription.side_effect = HTTPException(
            status_code=403, 
            detail="Active subscription required"
        )
        
        request_data = {
            "person_id": "person_123",
            "question": "Test question"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/chat", json=request_data, headers=headers)
        assert response.status_code == 403

    @patch('routes.chat.get_current_account')
    @patch('routes.chat.check_subscription_active')
    @patch('routes.chat.apply_rate_limiting')
    def test_chat_rate_limit_exceeded(self, mock_rate_limiting, mock_check_subscription,
                                    mock_get_account, client):
        """Test chat endpoint when rate limit is exceeded."""
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        mock_get_account.return_value = mock_account
        mock_check_subscription.return_value = None
        mock_rate_limiting.side_effect = HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
        
        request_data = {
            "person_id": "person_123",
            "question": "Test question"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/chat", json=request_data, headers=headers)
        assert response.status_code == 429

    @patch('routes.chat.apply_rate_limiting')
    @patch('routes.chat.check_subscription_active')
    @patch('routes.chat.ChatService')
    @patch('routes.chat.get_current_account')
    def test_chat_service_error(self, mock_get_account, mock_chat_service_class,
                               mock_check_subscription, mock_rate_limiting, client):
        """Test chat endpoint when chat service raises error."""
        # Setup mocks
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        mock_get_account.return_value = mock_account
        mock_rate_limiting.return_value = None
        mock_check_subscription.return_value = None
        
        # Mock chat service to raise error
        mock_chat_service = Mock()
        mock_chat_service.generate_response.side_effect = Exception("OpenAI API error")
        mock_chat_service_class.return_value = mock_chat_service
        
        request_data = {
            "person_id": "person_123",
            "question": "Test question"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/chat", json=request_data, headers=headers)
        assert response.status_code == 500

    def test_chat_invalid_request_format(self, client):
        """Test chat endpoint with invalid request format."""
        # Missing required fields
        request_data = {"question": "Test question"}  # Missing person_id
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/chat", json=request_data, headers=headers)
        assert response.status_code == 422

    def test_chat_question_too_long(self, client):
        """Test chat endpoint with question exceeding max length."""
        request_data = {
            "person_id": "person_123",
            "question": "x" * 1001  # Exceeds 1000 character limit
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/chat", json=request_data, headers=headers)
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.chat.get_current_account')
    def test_chat_database_error(self, mock_get_account, client):
        """Test chat endpoint when database error occurs."""
        mock_get_account.side_effect = Exception("Database connection failed")
        
        request_data = {
            "person_id": "person_123",
            "question": "Test question"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/chat", json=request_data, headers=headers)
        assert response.status_code == 500

    @patch('routes.chat.apply_rate_limiting')
    @patch('routes.chat.check_subscription_active')
    @patch('routes.chat.get_current_account')
    def test_chat_rate_limiting_error(self, mock_get_account, mock_check_subscription,
                                    mock_rate_limiting, client):
        """Test chat endpoint when rate limiting raises unexpected error."""
        mock_account = Account(
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        mock_get_account.return_value = mock_account
        mock_check_subscription.return_value = None
        mock_rate_limiting.side_effect = Exception("Redis connection failed")
        
        request_data = {
            "person_id": "person_123",
            "question": "Test question"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/chat", json=request_data, headers=headers)
        assert response.status_code == 500


class TestIntegration:
    """Test integration scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('routes.chat.apply_rate_limiting')
    @patch('routes.chat.check_subscription_active')
    @patch('routes.chat.ChatService')
    @patch('routes.chat.get_current_account')
    def test_complete_chat_workflow(self, mock_get_account, mock_chat_service_class,
                                  mock_check_subscription, mock_rate_limiting, client):
        """Test complete chat workflow from authentication to response."""
        # Setup account
        mock_account = Account(
            account_id=123,
            fub_account_id="fub_123",
            subscription_status=SubscriptionStatus.active
        )
        mock_get_account.return_value = mock_account
        
        # Setup middleware functions
        mock_rate_limiting.return_value = None
        mock_check_subscription.return_value = None
        
        # Setup chat service with realistic response
        mock_chat_service = Mock()
        mock_chat_service.generate_response.return_value = (
            "Based on the lead's recent activity, I suggest:\n"
            "• Send a personalized follow-up email\n"
            "• Schedule a phone call within 24 hours\n"
            "• Offer a free consultation"
        )
        mock_chat_service_class.return_value = mock_chat_service
        
        request_data = {
            "person_id": "lead_456",
            "question": "This lead viewed our pricing page twice. How should I follow up?"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.post("/chat", json=request_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "follow-up email" in data["answer"]
        assert data["person_id"] == "lead_456"
        
        # Verify all middleware was called
        mock_check_subscription.assert_called_once_with(mock_account)
        mock_rate_limiting.assert_called_once()
        mock_chat_service.generate_response.assert_called_once()

    @patch('routes.chat.get_current_account')
    def test_multiple_validation_failures(self, mock_get_account, client):
        """Test handling multiple validation failures."""
        # Test with both missing auth and invalid request
        request_data = {}  # Missing required fields
        
        # No auth header provided
        response = client.post("/chat", json=request_data)
        
        # Should fail on authentication first
        assert response.status_code in [401, 422] 